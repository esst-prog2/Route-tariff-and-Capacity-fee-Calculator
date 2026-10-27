"""Capacity Fee Calculator: price one product instrument at one point, or at
both sides of a bundled border point.

Public entry points are `resolve_period`, `calculate_fee`, `calculate_bundle_fee`
and `bundle_eur_total`; the calculations return a result or a `FeeError`
carrying a message for the user. Amounts stay in each side's own currency and
capacity unit; only a bundle's optional EUR total converts them."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Mapping

from . import periods
from .money import CURRENCY_DECIMALS, EUR, parse_fx_rate, parse_number, round_minor, round_places, split_by_weights
from .points import EUSTREAM, FGSZ, GASTRANS, GCA, NET4GAS, Bundle, Point
from .tariffs import HOURS_PER_UNIT, NoTariffRow, ProductPart, TariffTable

GAS_YEAR = "gas_year"
QUARTER = "quarter"
MONTH = "month"
DAY = "day"
INSTRUMENTS = (GAS_YEAR, QUARTER, MONTH, DAY)
INSTRUMENT_LABELS = {GAS_YEAR: "Gas year", QUARTER: "Quarter", MONTH: "Month", DAY: "Day"}

CAPACITY_MESSAGE = "Capacity must be a positive number."
# TSOs that bill the tariff cell rounded to this many decimals, not the cell as the file gives it.
TARIFF_DECIMALS = {GCA: 4}

# The products each TSO invoices in equal months (1/12 of a gas year, 1/3 of a quarter),
# at the tariff valid in that month, instead of by the month's number of days.
EQUAL_MONTH_INSTRUMENTS = {
    FGSZ: (GAS_YEAR, QUARTER),
    EUSTREAM: (GAS_YEAR, QUARTER),
    GCA: (GAS_YEAR, QUARTER),
    NET4GAS: (GAS_YEAR, QUARTER),
    GASTRANS: (QUARTER,),
}

CAPACITY_UNITS = ("kWh/h", "kWh/d")  # units the capacity can be typed in; tab 2 starts on the first


@dataclass(frozen=True)
class FeeError:
    message: str


@dataclass(frozen=True)
class NoTariffError(FeeError):
    """No tariff row applies to the point on a day of the product period."""

    day: date  # the first day of the period without a row


@dataclass(frozen=True)
class InvoiceLine:
    year: int
    month: int
    days: int
    amount: int  # minor units of the currency: whole HUF, else cents


@dataclass(frozen=True)
class FeeResult:
    point: Point
    instrument: str
    start: date
    end: date
    capacity_kwh_d: Fraction  # the requested capacity, converted to kWh/d if typed in kWh/h
    capacity: Fraction  # in `unit`
    unit: str  # kWh/h or kWh/d
    currency: str
    capacity_type: str
    price_column: str
    price: Fraction  # `currency` per 1 `unit` for the whole product period (weighted over `parts`)
    tariff_used: str
    exact_total: Fraction
    total: int  # minor units of the currency: whole HUF, else cents
    invoice: tuple[InvoiceLine, ...]
    parts: tuple[ProductPart, ...] = ()  # the stretches of the period priced from one row each
    part_prices: tuple[Fraction, ...] = ()  # the price cell of each part's row, as billed (see `tariff_decimals`)
    tariff_decimals: int | None = None  # the decimals the TSO rounds its tariff to, None when it bills the cell as is
    equal_months: bool = False  # each month is 1/12 (gas year) or 1/3 (quarter) of the product, not weighted by days


@dataclass(frozen=True)
class BundleFeeResult:
    bundle: Bundle
    exit: FeeResult
    entry: FeeResult

    @property
    def sides(self) -> tuple[FeeResult, FeeResult]:
        return self.exit, self.entry

    @property
    def rate_currencies(self) -> list[str]:
        """The side currencies that need a rate to EUR, in side order."""
        return list(dict.fromkeys(r.currency for r in self.sides if r.currency != EUR))


@dataclass(frozen=True)
class EurTotal:
    amount: int  # EUR cents
    rates: tuple[tuple[str, Fraction], ...]  # (currency, units per 1 EUR) used


@dataclass(frozen=True)
class RatesNeeded:
    missing: tuple[str, ...]  # currencies whose rate box is blank
    invalid: tuple[str, ...]  # currencies whose rate is not a positive number

    @property
    def message(self) -> str:
        parts = []
        if self.missing:
            names = " and ".join(f"{c} per EUR" for c in self.missing)
            parts.append(f"Enter the {names} rate{'s' if len(self.missing) > 1 else ''} to see the EUR total.")
        if self.invalid:
            names = " and ".join(f"{c} per EUR" for c in self.invalid)
            parts.append(f"The {names} rate must be a positive number.")
        return " ".join(parts)


def resolve_period(instrument: str, *, gas_year=None, year=None, quarter=None, month=None, day=None):
    """(start, end) of the chosen product period, or a FeeError when the
    selection is incomplete. `quarter` is the calendar quarter (Q4 = Oct-Dec)."""
    needed = {GAS_YEAR: (gas_year,), QUARTER: (year, quarter), MONTH: (year, month), DAY: (day,)}.get(instrument)
    if needed is None or None in needed:
        return FeeError("Choose a product period.")
    if instrument == GAS_YEAR:
        return periods.gas_year_period(gas_year)
    if instrument == QUARTER:
        return periods.quarter_period(year, quarter)
    if instrument == MONTH:
        return periods.month_first(year, month), periods.month_last(year, month)
    return day, day


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
    capacity_unit: str = "kWh/d",
) -> FeeResult | FeeError:
    """`capacity_text` is the requested capacity in `capacity_unit` (one of `CAPACITY_UNITS`)."""
    if capacity_unit not in CAPACITY_UNITS:
        raise ValueError(f"Unknown capacity unit {capacity_unit!r}")
    try:
        requested = parse_number(capacity_text)
    except ValueError:
        return FeeError(CAPACITY_MESSAGE)
    if requested <= 0:
        return FeeError(CAPACITY_MESSAGE)
    capacity_kwh_d = requested * HOURS_PER_UNIT[capacity_unit]
    if instrument not in INSTRUMENTS or start is None or end is None or end < start:
        return FeeError("Choose a product period.")

    decimals = TARIFF_DECIMALS.get(point.tso)

    def cell(row) -> Fraction:
        price = _price_cell(row, instrument, start)[1]
        return price if decimals is None else round_places(price, decimals)

    try:
        price, parts = table.product_price(*point.key, start, end, cell)
    except NoTariffRow as missing:
        return NoTariffError(
            f"No tariff exists for {point.tso_name} {point.cleaned_name} on {missing.day.isoformat()}.", missing.day)

    # Each month's own price: the cell of the row valid in it (day-weighted if a row changes inside the month).
    slices = periods.month_slices(start, end)
    month_prices = [
        sum((cell(p.row) * periods.days_in_period(max(p.first, s.first), min(p.last, s.last))
             for p in parts if p.first <= s.last and s.first <= p.last), Fraction(0)) / s.days
        for s in slices
    ]
    equal_months = instrument in EQUAL_MONTH_INSTRUMENTS.get(point.tso, ())
    if equal_months:
        # Every month counts the same, whatever its number of days.
        price = sum(month_prices, Fraction(0)) / len(slices)
        weights = month_prices
    else:
        # Each month's share of the total is its exact cost under the rows valid in it.
        weights = [month_price * s.days for month_price, s in zip(month_prices, slices)]

    row = parts[0].row
    column = _price_cell(row, instrument, start)[0]
    capacity = capacity_kwh_d / HOURS_PER_UNIT[row.unit]
    exact_total = capacity * price
    total = round_minor(exact_total, row.currency)

    if not any(weights):  # a zero price: split by days
        weights = [s.days for s in slices]
    amounts = split_by_weights(total, weights)
    invoice = tuple(InvoiceLine(s.year, s.month, s.days, a) for s, a in zip(slices, amounts))

    tariff_used = row.source_text() if len(parts) == 1 else "; ".join(
        f"{p.row.source_text()} for {dates_text(p.first, p.last)}" for p in parts)
    return FeeResult(
        point, instrument, start, end, capacity_kwh_d, capacity, row.unit, row.currency, row.capacity_type,
        column, price, tariff_used, exact_total, total, invoice, tuple(parts), tuple(cell(p.row) for p in parts),
        decimals, equal_months,
    )


def dates_text(first: date, last: date) -> str:
    return first.isoformat() if first == last else f"{first.isoformat()} to {last.isoformat()}"


def calculate_bundle_fee(
    table: TariffTable,
    bundle: Bundle,
    instrument: str,
    start: date,
    end: date,
    capacity_text,
    capacity_unit: str = "kWh/d",
) -> BundleFeeResult | FeeError:
    """Both sides priced independently for the same requested capacity, each in its own currency and unit."""
    results = []
    for side in bundle.sides:
        result = calculate_fee(table, side, instrument, start, end, capacity_text, capacity_unit)
        if isinstance(result, NoTariffError):
            side_text = "exit" if side.direction == "Exit" else "entry"
            return NoTariffError(f"No tariff exists for the {side.tso_name} {side_text} side "
                                 f"({side.cleaned_name}) on {result.day.isoformat()}.", result.day)
        if isinstance(result, FeeError):
            return result
        results.append(result)
    return BundleFeeResult(bundle, *results)


def bundle_eur_total(result: BundleFeeResult, rate_texts: Mapping[str, str]) -> EurTotal | RatesNeeded:
    """The bundle total in EUR cents, from the rounded side totals (so it matches
    the figures shown) and the typed rates (currency -> units per 1 EUR)."""
    rates: dict[str, Fraction] = {}
    missing, invalid = [], []
    for currency in result.rate_currencies:
        rate, message = parse_fx_rate(rate_texts.get(currency), currency)
        if message:
            invalid.append(currency)
        elif rate is None:
            missing.append(currency)
        else:
            rates[currency] = rate
    if missing or invalid:
        return RatesNeeded(tuple(missing), tuple(invalid))
    total = sum(
        (Fraction(r.total, 10 ** CURRENCY_DECIMALS[r.currency]) / (1 if r.currency == EUR else rates[r.currency])
         for r in result.sides),
        Fraction(0),
    )
    return EurTotal(round_minor(total, EUR), tuple(rates.items()))


def _earliest(table: TariffTable, booked: Point | Bundle) -> date | None:
    """The point's earliest row; for a bundle, the later of its sides' earliest rows."""
    sides = booked.sides if isinstance(booked, Bundle) else (booked,)
    earliest = [table.earliest_valid_from(*side.key) for side in sides]
    return None if None in earliest else max(earliest)


def gas_year_choices(table: TariffTable, booked: Point | Bundle, today: date) -> list[int]:
    """Gas years (by start year) from the earliest tariff row (of both sides,
    for a bundle) to two gas years after today's."""
    earliest = _earliest(table, booked)
    last = periods.gas_year_start_year(today) + 2
    first = periods.gas_year_start_year(earliest) if earliest else periods.gas_year_start_year(today)
    return list(range(first, last + 1))


def calendar_year_choices(table: TariffTable, booked: Point | Bundle, today: date) -> list[int]:
    """Calendar years covering those gas years (for the quarter and month pickers)."""
    gas_years = gas_year_choices(table, booked, today)
    return list(range(gas_years[0], gas_years[-1] + 2))
