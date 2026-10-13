"""Loading, validating and querying the tariff Excel export.

The export is wide: one row per point, direction, capacity type and validity
window, with one price column per product period. Loading narrows it to the
Entry/Exit rows of the three supported TSOs (Firm, or Interruptible where a
point has no Firm row) and exposes them as `TariffRow`s that are looked up by
(TSO, EIC, direction, date)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Mapping

import pandas as pd

from . import periods
from .money import to_fraction

SHEET_NAME = "Capacity_fee"
FIRM = "Firm"
INTERRUPTIBLE = "Interruptible"
SCOPE_DIRECTIONS = ("Entry", "Exit")
# Each TSO's rows must be in its own currency and capacity unit; nothing is converted.
TSO_FORMATS: Mapping[str, tuple[str, str]] = {
    "FGSZ": ("HUF", "kWh/h"),
    "Gastran": ("EUR", "kWh/h"),
    "BGTRGAZ": ("EUR", "kWh/d"),
}
# Rows left out on purpose, without a warning: Bulgartransgaz's earlier BGN tariffs.
SKIPPED_CURRENCIES: Mapping[str, tuple[str, ...]] = {"BGTRGAZ": ("BGN",)}

IDENTITY_COLUMNS = [
    "EIC", "Network point", "System operator", "Direction", "Currency",
    "Measure unit", "Capacity_type", "Valid from", "Valid to",
]
REQUIRED_COLUMNS = [*IDENTITY_COLUMNS, *periods.PRICE_COLUMNS]

PATH_ENV_VAR = "FGSZ_TARIFF_FILE"
DEFAULT_SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample" / "tariffs_sample.xlsx"


@dataclass(frozen=True)
class TariffRow:
    """One tariff row: the prices valid for a point (TSO, EIC, direction)."""

    operator: str
    eic: str
    direction: str
    valid_from: date
    valid_to: date | None  # None = open-ended
    prices: Mapping[str, Fraction] = field(compare=False)  # `currency` per 1 `unit` for the whole product period
    currency: str = "HUF"
    unit: str = "kWh/h"
    capacity_type: str = FIRM

    @property
    def key(self) -> tuple[str, str, str]:
        return self.operator, self.eic, self.direction

    @property
    def open_ended(self) -> bool:
        return self.valid_to is None

    def applies_on(self, day: date) -> bool:
        return self.valid_from <= day and (self.valid_to is None or day <= self.valid_to)

    def year_price(self) -> Fraction:
        return self.prices[periods.YEAR_COLUMN]

    def quarter_price(self, quarter: int) -> Fraction:
        return self.prices[periods.quarter_column(quarter)]

    def month_price(self, month: int) -> Fraction:
        return self.prices[periods.month_column(month)]

    def day_price(self, month: int) -> Fraction:
        return self.prices[periods.day_column(month)]

    def source_text(self) -> str:
        text = f"from {self.valid_from.isoformat()}"
        return text + " (open-ended)" if self.open_ended else text


class TariffTable:
    """Tariff rows grouped by point: (TSO, EIC, direction)."""

    def __init__(self, rows: list[TariffRow]):
        self._rows: dict[tuple[str, str, str], list[TariffRow]] = {}
        for row in sorted(rows, key=lambda r: r.valid_from):
            self._rows.setdefault(row.key, []).append(row)

    def __len__(self) -> int:
        return sum(len(rows) for rows in self._rows.values())

    def find_row(self, operator: str, eic: str, direction: str, day: date) -> TariffRow | None:
        """The row valid on `day` (a later row supersedes an earlier one)."""
        for row in reversed(self._rows.get((operator, eic, direction), [])):
            if row.applies_on(day):
                return row
        return None

    def earliest_valid_from(self, operator: str, eic: str, direction: str) -> date | None:
        rows = self._rows.get((operator, eic, direction))
        return rows[0].valid_from if rows else None

    def capacity_type(self, operator: str, eic: str, direction: str) -> str | None:
        """Firm or Interruptible (never mixed for one point); None when the point has no rows."""
        rows = self._rows.get((operator, eic, direction))
        return rows[0].capacity_type if rows else None

    def keys(self) -> list[tuple[str, str, str]]:
        return list(self._rows)


@dataclass
class LoadResult:
    table: TariffTable | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.table is not None


def resolve_tariff_path(environ: Mapping[str, str] | None = None) -> Path:
    """Configured tariff file: the environment variable, else the sample."""
    environ = os.environ if environ is None else environ
    configured = environ.get(PATH_ENV_VAR, "").strip()
    return Path(configured) if configured else DEFAULT_SAMPLE_PATH


def load_tariffs(source) -> LoadResult:
    """Load from a path or a file-like object. Never raises for bad input."""
    try:
        excel = pd.ExcelFile(source)
        sheet = SHEET_NAME if SHEET_NAME in excel.sheet_names else excel.sheet_names[0]
        frame = excel.parse(sheet)
    except Exception as exc:  # unreadable, wrong format, missing file ...
        return LoadResult(None, [f"The tariff file could not be read as an Excel file ({exc})."])
    return parse_frame(frame)


def parse_frame(frame: pd.DataFrame) -> LoadResult:
    frame = frame.copy()
    frame.columns = [str(c).strip() for c in frame.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        return LoadResult(None, [f"The tariff file is missing required column(s): {', '.join(missing)}."])

    for column in ("System operator", "Capacity_type", "Direction", "Currency", "Measure unit", "EIC"):
        frame[column] = frame[column].astype("string").str.strip()

    in_scope = _scope(frame)
    if in_scope.empty:
        return LoadResult(None, ["The tariff file has no FGSZ, Gastrans or Bulgartransgaz Entry/Exit rows."])

    rows: list[TariffRow] = []
    warnings: list[str] = []
    for index, record in in_scope.iterrows():
        row, problems = _parse_record(record)
        if row is not None:
            rows.append(row)
        else:
            number = int(index) + 2  # Excel row: header is row 1
            name = record["Network point"]
            warnings.append(f"Row {number} ({name}) was excluded: {'; '.join(problems)}.")

    if not rows:
        return LoadResult(None, ["No usable tariff rows were found.", *warnings])
    return LoadResult(TariffTable(rows), [], warnings)


def _scope(frame: pd.DataFrame) -> pd.DataFrame:
    """Entry/Exit rows of the supported TSOs, without the silently skipped
    currencies; per point (TSO, EIC, direction) its Firm rows, or its
    Interruptible rows when it has no Firm row."""
    operator = frame["System operator"]
    skipped = pd.Series(False, index=frame.index)
    for tso, currencies in SKIPPED_CURRENCIES.items():
        skipped |= ((operator == tso) & frame["Currency"].isin(currencies)).fillna(False).astype(bool)
    keep = (
        operator.isin(list(TSO_FORMATS))
        & frame["Direction"].isin(SCOPE_DIRECTIONS)
        & frame["Capacity_type"].isin([FIRM, INTERRUPTIBLE])
    ).fillna(False).astype(bool)
    rows = frame[keep & ~skipped]
    point = [rows[c].fillna("") for c in ("System operator", "EIC", "Direction")]
    is_firm = (rows["Capacity_type"] == FIRM).astype(bool)
    has_firm = is_firm.groupby(point).transform("any").astype(bool)
    return rows[is_firm == has_firm]


def _parse_record(record) -> tuple[TariffRow | None, list[str]]:
    problems: list[str] = []

    eic = record["EIC"]
    if pd.isna(eic) or not str(eic).strip():
        problems.append("EIC is blank")
    operator = str(record["System operator"])
    currency, unit = TSO_FORMATS[operator]
    if record["Currency"] != currency:
        problems.append(f"currency is {record['Currency']!s}, only {currency} is supported for {operator}")
    if record["Measure unit"] != unit:
        problems.append(f"unit is {record['Measure unit']!s}, only {unit} is supported for {operator}")

    valid_from = pd.to_datetime(record["Valid from"], errors="coerce")
    if pd.isna(valid_from):
        problems.append("'Valid from' is blank or not a date")
    valid_to = None
    if not pd.isna(record["Valid to"]):
        parsed = pd.to_datetime(record["Valid to"], errors="coerce")
        if pd.isna(parsed):
            problems.append("'Valid to' is not a date")
        else:
            valid_to = parsed.date()
    if not pd.isna(valid_from) and valid_to is not None and valid_to < valid_from.date():
        problems.append("'Valid to' is before 'Valid from'")

    prices: dict[str, Fraction] = {}
    bad_prices: list[str] = []
    for column in periods.PRICE_COLUMNS:
        number = pd.to_numeric(record[column], errors="coerce")
        if pd.isna(number) or number < 0:
            bad_prices.append(column)
        else:
            prices[column] = to_fraction(float(number))
    if bad_prices:
        problems.append(f"blank, negative or non-numeric price in {', '.join(bad_prices)}")

    if problems:
        return None, problems
    row = TariffRow(
        operator, str(eic).strip(), str(record["Direction"]), valid_from.date(), valid_to, prices,
        currency, unit, str(record["Capacity_type"]),
    )
    return row, []
