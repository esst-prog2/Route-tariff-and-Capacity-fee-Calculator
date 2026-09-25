"""Route Tariff Calculator: one entry point + one exit point + a booking period.

Public entry point is `calculate_route`, which returns a `RouteResult` or a
`RouteError` carrying a message for the user; it does not raise for bad input."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction

from . import periods
from .money import parse_number
from .optimizer import Plan, optimize
from .points import ENTRY, EXIT, Point
from .tariffs import TariffRow, TariffTable

FX_MESSAGE = "The FX rate must be a positive number (HUF per 1 EUR)."


@dataclass(frozen=True)
class RouteError:
    message: str


class NoTariffError(Exception):
    """Internal: no tariff row applies to a point on a date."""

    def __init__(self, point: Point, day: date):
        super().__init__(f"No tariff exists for {point.cleaned_name} on {day.isoformat()}.")
        self.message = str(self)


class RouteOracle:
    """Route prices: the entry price plus the exit price for the same product.

    Each product is priced from the row valid on its first day."""

    def __init__(self, table: TariffTable, entry: Point, exit_: Point):
        self._table = table
        self._entry = entry
        self._exit = exit_

    def _row(self, point: Point, day: date) -> TariffRow:
        row = self._table.find_row(point.eic, point.direction, day)
        if row is None:
            raise NoTariffError(point, day)
        return row

    def _sum(self, day: date, getter) -> Fraction:
        return getter(self._row(self._entry, day)) + getter(self._row(self._exit, day))

    def day_price(self, day: date) -> Fraction:
        return self._sum(day, lambda row: row.day_price(day.month))

    def month_price(self, year: int, month: int) -> Fraction:
        return self._sum(periods.month_first(year, month), lambda row: row.month_price(month))

    def quarter_price(self, year: int, quarter: int) -> Fraction:
        first, _ = periods.quarter_period(year, quarter)
        return self._sum(first, lambda row: row.quarter_price(quarter))

    def tariff_used(self, first: date, last: date) -> str:
        parts = []
        for label, point in (("entry", self._entry), ("exit", self._exit)):
            sources: list[str] = []
            for day in periods.iter_days(first, last):
                text = self._row(point, day).source_text()
                if text not in sources:
                    sources.append(text)
            parts.append(f"{label} {', '.join(sources)}")
        return "; ".join(parts)


@dataclass(frozen=True)
class RouteResult:
    entry: Point
    exit: Point
    plan: Plan
    fx_rate: Fraction | None  # HUF per EUR, None when not entered or invalid
    fx_message: str | None  # set when a rate was typed but is not usable

    @property
    def days(self) -> int:
        return self.plan.days

    @property
    def huf_per_kwh_h(self) -> Fraction:
        return self.plan.total

    @property
    def huf_per_mwh(self) -> Fraction:
        """Booking cost over the energy 1 kWh/h could carry in the period
        (24 h x days), i.e. 100 % utilisation."""
        return self.plan.total / (24 * self.days) * 1000

    @property
    def all_daily_huf_per_mwh(self) -> Fraction:
        return self.plan.all_daily_total / (24 * self.days) * 1000

    @property
    def eur_per_mwh(self) -> Fraction | None:
        return None if self.fx_rate is None else self.huf_per_mwh / self.fx_rate

    @property
    def all_daily_eur_per_mwh(self) -> Fraction | None:
        return None if self.fx_rate is None else self.all_daily_huf_per_mwh / self.fx_rate


def parse_fx_rate(text) -> tuple[Fraction | None, str | None]:
    """(rate, None) for a positive number, (None, None) for a blank box,
    (None, message) for anything else."""
    if text is None or not str(text).strip():
        return None, None
    try:
        rate = parse_number(text)
    except ValueError:
        return None, FX_MESSAGE
    if rate <= 0:
        return None, FX_MESSAGE
    return rate, None


def calculate_route(
    table: TariffTable,
    entry: Point,
    exit_: Point,
    start: date | None,
    end: date | None,
    fx_rate_text="",
) -> RouteResult | RouteError:
    if start is None or end is None:
        return RouteError("The period is invalid: enter a valid start date and end date.")
    if end < start:
        return RouteError("The period is invalid: the end date is before the start date.")
    if entry.direction != ENTRY or exit_.direction != EXIT:
        return RouteError("This route is not possible: a route needs one entry point and one exit point.")
    if entry.eic == exit_.eic:
        return RouteError(
            f"This route is not possible: {entry.cleaned_name} and {exit_.cleaned_name} "
            "are the same physical point."
        )

    try:
        plan = optimize(start, end, RouteOracle(table, entry, exit_))
    except NoTariffError as error:
        return RouteError(error.message)

    fx_rate, fx_message = parse_fx_rate(fx_rate_text)
    return RouteResult(entry, exit_, plan, fx_rate, fx_message)
