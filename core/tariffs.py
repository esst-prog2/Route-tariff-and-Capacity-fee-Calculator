"""Loading, validating and querying the tariff Excel export.

The export is wide: one row per point, direction, capacity type and validity
window, with one price column per product period. Loading narrows it to the
Entry/Exit rows of the supported TSOs (Firm, or Interruptible where a
point has no Firm row) and exposes them as `TariffRow`s that are looked up by
(TSO, EIC, direction, date)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd

from . import periods
from .money import to_fraction

SHEET_NAME = "Capacity_fee"
FIRM = "Firm"
INTERRUPTIBLE = "Interruptible"
SCOPE_DIRECTIONS = ("Entry", "Exit")
# The TSOs in scope, by their `System operator` code: display name, and the currency and
# capacity unit their rows must be in (nothing is converted). Any other operator is ignored.
TSOS: Mapping[str, tuple[str, str, str]] = {
    "AMBERGR": ("Amber Grid", "EUR", "kWh/h"),
    "BGTRGAZ": ("Bulgartransgaz", "EUR", "kWh/d"),
    "DESFA": ("DESFA", "EUR", "kWh/h"),
    "EUSTR": ("Eustream", "EUR", "kWh/h"),
    "FGSZ": ("FGSZ", "HUF", "kWh/h"),
    "GASCADE": ("GASCADE", "EUR", "kWh/h"),
    "GAZSYS": ("GAZ-SYSTEM", "PLN", "kWh/h"),
    "GCA": ("Gas Connect Austria", "EUR", "kWh/h"),
    "GTS": ("Gasunie Transport Services", "EUR", "kWh/h"),
    "Gastran": ("Gastrans", "EUR", "kWh/h"),
    "Gasunie": ("Gasunie Deutschland", "EUR", "kWh/h"),
    "ICGB": ("ICGB", "EUR", "kWh/d"),
    "NET4GAS": ("NET4GAS", "CZK", "kWh/h"),
    "OGE": ("Open Grid Europe", "EUR", "kWh/h"),
    "Plinovo": ("Plinovodi", "EUR", "kWh/h"),
    "TAG": ("Trans Austria Gasleitung", "EUR", "kWh/h"),
    "TAP": ("Trans Adriatic Pipeline", "EUR", "kWh/d"),
    "TRANSGA": ("Transgaz", "RON", "kWh/h"),
    "UKRTRAG": ("Gas TSO of Ukraine", "EUR", "kWh/d"),
    "plinacr": ("Plinacro", "EUR", "kWh/d"),
    "snam": ("Snam Rete Gas", "EUR", "kWh/h"),
}
TSO_NAMES: Mapping[str, str] = {code: name for code, (name, _, _) in TSOS.items()}
TSO_FORMATS: Mapping[str, tuple[str, str]] = {code: (currency, unit) for code, (_, currency, unit) in TSOS.items()}
# The energy one unit of each capacity unit carries per day, in kWh (so 1 kWh/h = 24 kWh/d).
HOURS_PER_UNIT: Mapping[str, int] = {"kWh/h": 24, "kWh/d": 1}
# Rows left out on purpose, without a warning: the pre-euro BGN and HRK tariffs.
SKIPPED_CURRENCIES: Mapping[str, tuple[str, ...]] = {"BGTRGAZ": ("BGN",), "plinacr": ("HRK",)}

IDENTITY_COLUMNS = [
    "EIC", "Network point", "System operator", "Direction", "Currency",
    "Measure unit", "Capacity_type", "Valid from", "Valid to",
]
REQUIRED_COLUMNS = [*IDENTITY_COLUMNS, *periods.PRICE_COLUMNS]

PATH_ENV_VAR = "FGSZ_TARIFF_FILE"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_PATH = DATA_DIR / "real" / "tariffs_real.xlsx"
DEFAULT_SAMPLE_PATH = DATA_DIR / "sample" / "tariffs_sample.xlsx"  # synthetic; the tests' data


@dataclass(frozen=True)
class TariffRow:
    """One tariff row: the prices valid for a point (TSO, EIC, direction)."""

    operator: str
    eic: str
    direction: str
    valid_from: date
    valid_to: date | None  # None = open-ended
    prices: Mapping[str, Fraction] = field(compare=False)  # `currency` per 1 `unit` for the whole product period
    currency: str
    unit: str
    capacity_type: str
    network_point: str = field(compare=False)  # the source `Network point` text

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


class NoTariffRow(LookupError):
    """No tariff row applies to a point on `day`."""

    def __init__(self, day: date):
        super().__init__(day.isoformat())
        self.day = day


@dataclass(frozen=True)
class ProductPart:
    """Days first..last of a product period, all priced from one row."""

    first: date
    last: date
    row: TariffRow

    @property
    def days(self) -> int:
        return periods.days_in_period(self.first, self.last)


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

    def product_parts(self, operator: str, eic: str, direction: str, first: date, last: date) -> list[ProductPart]:
        """Days first..last split where the applicable row changes. Raises
        NoTariffRow for the first day no row applies to."""
        rows = self._rows.get((operator, eic, direction), [])
        changes = {r.valid_from for r in rows} | {r.valid_to + timedelta(days=1) for r in rows if r.valid_to}
        starts = [first, *sorted(day for day in changes if first < day <= last)]
        parts: list[ProductPart] = []
        for i, start in enumerate(starts):
            end = starts[i + 1] - timedelta(days=1) if i + 1 < len(starts) else last
            row = self.find_row(operator, eic, direction, start)
            if row is None:
                raise NoTariffRow(start)
            if parts and parts[-1].row is row:
                parts[-1] = ProductPart(parts[-1].first, end, row)
            else:
                parts.append(ProductPart(start, end, row))
        return parts

    def product_price(
        self, operator: str, eic: str, direction: str, first: date, last: date, cell: Callable[[TariffRow], Fraction],
    ) -> tuple[Fraction, list[ProductPart]]:
        """The price of the product covering first..last: each part's `cell`
        weighted by its share of the product's days (the cell itself when one
        row covers the whole period)."""
        parts = self.product_parts(operator, eic, direction, first, last)
        days = periods.days_in_period(first, last)
        return sum((cell(part.row) * part.days / days for part in parts), Fraction(0)), parts

    def earliest_valid_from(self, operator: str, eic: str, direction: str) -> date | None:
        rows = self._rows.get((operator, eic, direction))
        return rows[0].valid_from if rows else None

    def capacity_type(self, operator: str, eic: str, direction: str) -> str | None:
        """Firm or Interruptible (never mixed for one point); None when the point has no rows."""
        rows = self._rows.get((operator, eic, direction))
        return rows[0].capacity_type if rows else None

    def keys(self) -> list[tuple[str, str, str]]:
        return list(self._rows)

    def network_point(self, operator: str, eic: str, direction: str) -> str:
        """The source `Network point` text of the point's latest row."""
        rows = self._rows.get((operator, eic, direction))
        return rows[-1].network_point if rows else ""


@dataclass
class LoadResult:
    table: TariffTable | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.table is not None


def resolve_tariff_path(environ: Mapping[str, str] | None = None) -> Path:
    """Configured tariff file: the environment variable, else the real tariffs."""
    environ = os.environ if environ is None else environ
    configured = environ.get(PATH_ENV_VAR, "").strip()
    return Path(configured) if configured else DEFAULT_PATH


def load_tariffs(source) -> LoadResult:
    """Load from a path or a file-like object. Never raises for bad input."""
    try:
        excel = pd.ExcelFile(source)
        sheet = SHEET_NAME if SHEET_NAME in excel.sheet_names else excel.sheet_names[0]
        frame = excel.parse(sheet)
    except Exception as exc:  # unreadable, wrong format, missing file ...
        return LoadResult(None, [f"The tariff file could not be read as an Excel file ({exc})."])
    result = parse_frame(frame)
    if sheet != SHEET_NAME:
        result.warnings.insert(0, f"The file has no '{SHEET_NAME}' sheet, so its first sheet '{sheet}' was read.")
    return result


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
        return LoadResult(None, ["The tariff file has no Entry/Exit rows of a supported TSO."])

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
        currency, unit, str(record["Capacity_type"]), str(record["Network point"]).strip(),
    )
    return row, []
