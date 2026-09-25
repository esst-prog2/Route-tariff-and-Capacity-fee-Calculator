"""Capacity Fee Calculator: price one product instrument at one point.

Public entry points are `resolve_period` and `calculate_fee`; `calculate_fee`
returns a `FeeResult` or a `FeeError` carrying a message for the user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction

from . import periods
from .money import parse_number, round_whole, split_by_weights
from .points import Point
from .tariffs import TariffTable

GAS_YEAR = "gas_year"
QUARTER = "quarter"
MONTH = "month"
DAY = "day"
INSTRUMENTS = (GAS_YEAR, QUARTER, MONTH, DAY)
INSTRUMENT_LABELS = {GAS_YEAR: "Gas year", QUARTER: "Quarter", MONTH: "Month", DAY: "Day"}

CAPACITY_MESSAGE = "Capacity must be a positive number (kWh/d)."
HOURS_PER_DAY = 24


@dataclass(frozen=True)
class FeeError:
    message: str


@dataclass(frozen=True)
class InvoiceLine:
    year: int
    month: int
    days: int
    amount: int  # whole HUF


@dataclass(frozen=True)
class FeeResult:
    point: Point
    instrument: str
    start: date
    end: date
    capacity_kwh_d: Fraction
    capacity_kwh_h: Fraction
    price_column: str
    price: Fraction  # HUF per 1 kWh/h for the whole product period
    tariff_used: str
    exact_total: Fraction
    total: int  # whole HUF
    invoice: tuple[InvoiceLine, ...]


def resolve_period(instrument: str, *, gas_year=None, year=None, quarter=None, month=None, day=None):
    """(start, end) of the chosen product period, or a FeeError when the
    selection is incomplete. `quarter` is the calendar quarter (Q4 = Oct-Dec)."""
    try:
        if instrument == GAS_YEAR:
            return periods.gas_year_period(gas_year)
        if instrument == QUARTER:
            return periods.quarter_period(year, quarter)
        if instrument == MONTH:
            return periods.month_first(year, month), periods.month_last(year, month)
        if instrument == DAY:
            return (day, day) if day is not None else FeeError("Choose a product period.")
    except (TypeError, ValueError):
        pass
    return FeeError("Choose a product period.")


def _price_cell(row, instrument: str, start: date) -> tuple[str, Fraction]:
    if instrument == GAS_YEAR:
        return periods.YEAR_COLUMN, row.year_price()
    if instrument == QUARTER:
        quarter = periods.quarter_of_month(start.month)
        return periods.quarter_column(quarter), row.quarter_price(quarter)
    if instrument == MONTH:
        return periods.month_column(start.month), row.month_price(start.month)
    return periods.day_column(start.month), row.day_price(start.month)


def calculate_fee(
    table: TariffTable,
    point: Point,
    instrument: str,
    start: date,
    end: date,
    capacity_text,
) -> FeeResult | FeeError:
    try:
        capacity_kwh_d = parse_number(capacity_text)
    except ValueError:
        return FeeError(CAPACITY_MESSAGE)
    if capacity_kwh_d <= 0:
        return FeeError(CAPACITY_MESSAGE)
    if instrument not in INSTRUMENTS or start is None or end is None or end < start:
        return FeeError("Choose a product period.")

    row = table.find_row(point.eic, point.direction, start)
    if row is None:
        return FeeError(f"No tariff exists for {point.cleaned_name} on {start.isoformat()}.")

    column, price = _price_cell(row, instrument, start)
    capacity_kwh_h = capacity_kwh_d / HOURS_PER_DAY
    exact_total = capacity_kwh_h * price
    total = round_whole(exact_total)

    slices = periods.month_slices(start, end)
    amounts = split_by_weights(total, [s.days for s in slices])
    invoice = tuple(InvoiceLine(s.year, s.month, s.days, a) for s, a in zip(slices, amounts))

    return FeeResult(
        point, instrument, start, end, capacity_kwh_d, capacity_kwh_h,
        column, price, row.source_text(), exact_total, total, invoice,
    )


def gas_year_choices(table: TariffTable, point: Point, today: date) -> list[int]:
    """Gas years (by start year) from the point's earliest tariff row to two
    gas years after today's."""
    earliest = table.earliest_valid_from(point.eic, point.direction)
    last = periods.gas_year_start_year(today) + 2
    first = periods.gas_year_start_year(earliest) if earliest else periods.gas_year_start_year(today)
    return list(range(first, last + 1))


def calendar_year_choices(table: TariffTable, point: Point, today: date) -> list[int]:
    """Calendar years covering those gas years (for the quarter and month pickers)."""
    gas_years = gas_year_choices(table, point, today)
    return list(range(gas_years[0], gas_years[-1] + 2))
