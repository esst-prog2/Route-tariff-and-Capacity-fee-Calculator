"""Route Tariff Calculator: a hub-to-hub route along the HU - RS - BG corridor
plus a booking period.

The route's points are grouped by TSO; each TSO is optimised on its own, in
its own currency and capacity unit, and only the per-MWh results are turned
into EUR and added up. Public entry point is `calculate_route`, which returns
a `RouteResult` or a `RouteError` carrying a message for the user; it does
not raise for bad input."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction

from . import periods, points
from .money import parse_number
from .optimizer import Plan, PriceUnavailable, optimize
from .points import Point
from .tariffs import TSO_FORMATS, TariffRow, TariffTable

FX_MESSAGE = "The FX rate must be a positive number (HUF per 1 EUR)."
HOURS_PER_UNIT = {"kWh/h": 24, "kWh/d": 1}  # energy one unit of capacity carries per day, in kWh


@dataclass(frozen=True)
class RouteError:
    message: str


class NoTariffError(PriceUnavailable):
    """Internal: no tariff row applies to a point on a date."""

    def __init__(self, point: Point, day: date):
        super().__init__(f"No tariff exists for {point.tso_name} {point.cleaned_name} on {day.isoformat()}.")
        self.message = str(self)


class TsoOracle:
    """One TSO's prices on a route: the sum of the same product's prices at
    each of the TSO's points, in the TSO's currency per 1 unit of its capacity.

    Each product is priced from the row valid on its first day."""

    def __init__(self, table: TariffTable, tso_points: list[Point]):
        self._table = table
        self._points = tso_points

    def _row(self, point: Point, day: date) -> TariffRow:
        row = self._table.find_row(*point.key, day)
        if row is None:
            raise NoTariffError(point, day)
        return row

    def _sum(self, day: date, getter) -> Fraction:
        return sum((getter(self._row(point, day)) for point in self._points), Fraction(0))

    def day_price(self, day: date) -> Fraction:
        return self._sum(day, lambda row: row.day_price(day.month))

    def month_price(self, year: int, month: int) -> Fraction:
        return self._sum(periods.month_first(year, month), lambda row: row.month_price(month))

    def quarter_price(self, year: int, quarter: int) -> Fraction:
        first, _ = periods.quarter_period(year, quarter)
        return self._sum(first, lambda row: row.quarter_price(quarter))

    def tariff_used(self, first: date, last: date) -> str:
        parts = []
        for point in self._points:
            sources: list[str] = []
            for day in periods.iter_days(first, last):
                text = self._row(point, day).source_text()
                if text not in sources:
                    sources.append(text)
            parts.append(f"{point.direction.lower()} {', '.join(sources)}")
        return "; ".join(parts)


@dataclass(frozen=True)
class TsoLeg:
    """One TSO's part of a route: its points and its cheapest plan."""

    tso: str
    points: tuple[Point, ...]
    plan: Plan
    fx_rate: Fraction | None  # HUF per EUR; only used for a HUF leg

    @property
    def tso_name(self) -> str:
        return points.tso_name(self.tso)

    @property
    def currency(self) -> str:
        return TSO_FORMATS[self.tso][0]

    @property
    def unit(self) -> str:
        return TSO_FORMATS[self.tso][1]

    def _per_mwh(self, cost: Fraction) -> Fraction:
        """Cost over the energy one unit of capacity could carry on the
        requested days (100 % utilisation), in the TSO's currency per MWh."""
        return cost / (HOURS_PER_UNIT[self.unit] * self.plan.days) * 1000

    def _to_eur(self, value: Fraction) -> Fraction | None:
        if self.currency == "EUR":
            return value
        return None if self.fx_rate is None else value / self.fx_rate

    @property
    def per_mwh(self) -> Fraction:
        return self._per_mwh(self.plan.total)

    @property
    def all_daily_per_mwh(self) -> Fraction:
        return self._per_mwh(self.plan.all_daily_total)

    @property
    def eur_per_mwh(self) -> Fraction | None:
        return self._to_eur(self.per_mwh)

    @property
    def all_daily_eur_per_mwh(self) -> Fraction | None:
        return self._to_eur(self.all_daily_per_mwh)


@dataclass(frozen=True)
class RouteResult:
    begin: str
    end: str
    points: tuple[Point, ...]
    legs: tuple[TsoLeg, ...]
    fx_rate: Fraction | None  # HUF per EUR, None when not entered, invalid or not needed
    fx_message: str | None  # set when a rate was typed but is not usable

    @property
    def needs_fx(self) -> bool:
        return any(leg.currency == "HUF" for leg in self.legs)

    @property
    def days(self) -> int:
        return self.legs[0].plan.days

    @staticmethod
    def _sum(values) -> Fraction | None:
        values = list(values)
        return None if any(v is None for v in values) else sum(values, Fraction(0))

    @property
    def eur_per_mwh(self) -> Fraction | None:
        return self._sum(leg.eur_per_mwh for leg in self.legs)

    @property
    def all_daily_eur_per_mwh(self) -> Fraction | None:
        return self._sum(leg.all_daily_eur_per_mwh for leg in self.legs)

    @property
    def saving_eur_per_mwh(self) -> Fraction | None:
        if self.eur_per_mwh is None:
            return None
        return self.all_daily_eur_per_mwh - self.eur_per_mwh


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


def group_by_tso(route: list[Point]) -> list[tuple[str, list[Point]]]:
    """The route's points grouped by TSO, in the order the TSOs are met."""
    groups: dict[str, list[Point]] = {}
    for point in route:
        groups.setdefault(point.tso, []).append(point)
    return list(groups.items())


def calculate_route(
    table: TariffTable,
    begin: str,
    end_country: str,
    start: date | None,
    end: date | None,
    fx_rate_text="",
) -> RouteResult | RouteError:
    if begin == end_country:
        return RouteError(f"This route is not possible: it begins and ends in {begin}, so it crosses no border.")
    try:
        route = points.route_points(begin, end_country)
    except ValueError:
        return RouteError(f"This route is not possible: {begin} to {end_country} is not on the HU - RS - BG corridor.")
    if start is None or end is None:
        return RouteError("The period is invalid: enter a valid start date and end date.")
    if end < start:
        return RouteError("The period is invalid: the end date is before the start date.")

    groups = group_by_tso(route)
    needs_fx = any(TSO_FORMATS[tso][0] == "HUF" for tso, _ in groups)
    fx_rate, fx_message = parse_fx_rate(fx_rate_text) if needs_fx else (None, None)

    legs = []
    for tso, tso_points in groups:
        try:
            plan = optimize(start, end, TsoOracle(table, tso_points))
        except NoTariffError as error:
            return RouteError(error.message)
        legs.append(TsoLeg(tso, tuple(tso_points), plan, fx_rate))

    return RouteResult(begin, end_country, tuple(route), tuple(legs), fx_rate, fx_message)
