"""Route Tariff Calculator: a hub-to-hub route from a beginning country across
chosen border points of the network, plus a booking period.

The route's points are grouped by TSO; each TSO is optimised on its own, in
its own currency and capacity unit, and only the per-MWh results are turned
into EUR and added up. Public entry point is `calculate_route`, which returns
a `RouteResult` or a `RouteError` carrying a message for the user; it does
not raise for bad input."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Mapping

from . import periods, points
from .money import EUR, parse_fx_rate
from .optimizer import DAILY, MONTHLY, PRODUCTS, QUARTERLY, YEARLY, Plan, PriceUnavailable, Segment, optimize
from .points import Point
from .tariffs import HOURS_PER_UNIT, TSO_FORMATS, NoTariffRow, TariffRow, TariffTable

FIRST_POINT_MESSAGE = "Choose the first border point of the route on the map or in the Next point list."


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

    A product whose period crosses a tariff change is priced part by part
    (see `TariffTable.product_price`)."""

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

    def _product(self, first: date, last: date, cell) -> Fraction:
        """A yearly, quarterly or monthly product's price over first..last,
        each point's cell weighted by the days of each row it crosses."""
        total = Fraction(0)
        for point in self._points:
            try:
                total += self._table.product_price(*point.key, first, last, cell)[0]
            except NoTariffRow as missing:
                raise NoTariffError(point, missing.day) from None
        return total

    def month_price(self, year: int, month: int) -> Fraction:
        first, last = periods.month_first(year, month), periods.month_last(year, month)
        return self._product(first, last, lambda row: row.month_price(month))

    def quarter_price(self, year: int, quarter: int) -> Fraction:
        first, last = periods.quarter_period(year, quarter)
        return self._product(first, last, lambda row: row.quarter_price(quarter))

    def year_price(self, gas_year: int) -> Fraction:
        first, last = periods.gas_year_period(gas_year)
        return self._product(first, last, lambda row: row.year_price())

    def sources(self, point: Point, first: date, last: date) -> str:
        """The rows one point's prices come from on days first..last."""
        sources: list[str] = []
        for day in periods.iter_days(first, last):
            text = self._row(point, day).source_text()
            if text not in sources:
                sources.append(text)
        return ", ".join(sources)

    def tariff_used(self, first: date, last: date) -> str:
        return "; ".join(f"{point.direction.lower()} {self.sources(point, first, last)}" for point in self._points)


def segment_price(oracle: TsoOracle, segment: Segment) -> Fraction:
    """The oracle's price for the product a segment books (used to cost one
    point of a TSO for the products chosen for the whole TSO)."""
    first = segment.start
    if segment.product == YEARLY:
        return oracle.year_price(periods.gas_year_start_year(first))
    if segment.product == QUARTERLY:
        return oracle.quarter_price(first.year, periods.quarter_of_month(first.month))
    if segment.product == MONTHLY:
        return oracle.month_price(first.year, first.month)
    return sum((oracle.day_price(d) for d in periods.iter_days(segment.start, segment.end)), Fraction(0))


def _segment_cell(segment: Segment):
    """The price cell a yearly, quarterly or monthly segment books."""
    month = segment.start.month
    if segment.product == YEARLY:
        return lambda row: row.year_price()
    if segment.product == QUARTERLY:
        return lambda row: row.quarter_price(periods.quarter_of_month(month))
    return lambda row: row.month_price(month)


def point_tariff_used(table: TariffTable, point: Point, segment: Segment) -> str:
    """The tariff rows behind one point's price for a booked product: every
    row valid during the product (or during the daily days)."""
    return TsoOracle(table, [point]).sources(point, segment.start, segment.end)


def point_tariff(table: TariffTable, point: Point, segment: Segment) -> tuple[Fraction, ...]:
    """One point's tariff for a booked product, in its own currency and unit:
    the product's cell of each row it is priced from (one value unless the
    product crosses a tariff change), or the distinct day prices of a daily
    stretch."""
    if segment.product != DAILY:
        cell = _segment_cell(segment)
        prices = [cell(part.row) for part in table.product_parts(*point.key, segment.start, segment.end)]
    else:
        oracle = TsoOracle(table, [point])
        prices = [oracle.day_price(day) for day in periods.iter_days(segment.start, segment.end)]
    return tuple(dict.fromkeys(prices))


@dataclass(frozen=True)
class TsoLeg:
    """One TSO's part of a route: its points and its cheapest plan."""

    tso: str
    points: tuple[Point, ...]
    plan: Plan
    fx_rate: Fraction | None  # units of the leg's currency per EUR; None for EUR or while missing
    point_costs: tuple[Fraction, ...] = ()  # each point's own price for the chosen products, in `points` order
    comparison: Plan | None = None  # cheapest plan without the plan's longest product; None when daily only

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
        if self.currency == EUR:
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

    @property
    def point_eur_per_mwh(self) -> tuple[Fraction | None, ...]:
        return tuple(self._to_eur(self._per_mwh(cost)) for cost in self.point_costs)

    @property
    def longest_product(self) -> str:
        return max((seg.product for seg in self.plan.segments), key=PRODUCTS.index)

    @property
    def comparison_eur_per_mwh(self) -> Fraction | None:
        """The comparison plan's EUR/MWh, or the cheapest one when there is none."""
        return self._to_eur(self._per_mwh(self.comparison.total)) if self.comparison else self.eur_per_mwh


@dataclass(frozen=True)
class RouteResult:
    begin: str
    end: str
    route_text: str  # e.g. "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"
    points: tuple[Point, ...]
    legs: tuple[TsoLeg, ...]
    rates: tuple[tuple[str, Fraction | None], ...]  # each non-EUR currency on the route and its usable rate
    invalid_rates: tuple[str, ...] = ()  # currencies whose typed rate is not a positive number

    @property
    def rate_currencies(self) -> list[str]:
        return [currency for currency, _ in self.rates]

    @property
    def missing_rates(self) -> list[str]:
        """Currencies whose box is still blank."""
        return [c for c, rate in self.rates if rate is None and c not in self.invalid_rates]

    @property
    def rates_used(self) -> list[tuple[str, Fraction]]:
        return [(c, rate) for c, rate in self.rates if rate is not None]

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

    @property
    def has_comparison(self) -> bool:
        return any(leg.comparison for leg in self.legs)

    @property
    def comparison_eur_per_mwh(self) -> Fraction | None:
        """Sum over the TSOs of their next-shorter comparison (or cheapest) EUR/MWh."""
        if not self.has_comparison:
            return None
        return self._sum(leg.comparison_eur_per_mwh for leg in self.legs)

    @property
    def comparison_saving_eur_per_mwh(self) -> Fraction | None:
        if self.comparison_eur_per_mwh is None or self.eur_per_mwh is None:
            return None
        return self.comparison_eur_per_mwh - self.eur_per_mwh

    def _compared(self) -> dict[str, list[str]]:
        """Excluded product type -> the TSOs compared without it, longest type first."""
        groups: dict[str, list[str]] = {}
        for leg in self.legs:
            if leg.comparison:
                groups.setdefault(leg.longest_product, []).append(leg.tso_name)
        return dict(sorted(groups.items(), key=lambda item: -PRODUCTS.index(item[0])))

    @property
    def comparison_label(self) -> str | None:
        groups = self._compared()
        if not groups:
            return None
        return f"Without {next(iter(groups))} products" if len(groups) == 1 else "Next shorter products"

    @property
    def comparison_note(self) -> str | None:
        """Which TSO is compared without which product, when they differ."""
        groups = self._compared()
        if len(groups) < 2:
            return None
        return "; ".join(f"{', '.join(names)} without {product}" for product, names in groups.items())


def group_by_tso(route: list[Point]) -> list[tuple[str, list[Point]]]:
    """The route's points grouped by TSO, in the order the TSOs are met."""
    groups: dict[str, list[Point]] = {}
    for point in route:
        groups.setdefault(point.tso, []).append(point)
    return list(groups.items())


def calculate_route(
    table: TariffTable,
    begin: str,
    route_points: list[str],
    start: date | None,
    end: date | None,
    rate_texts: Mapping[str, str] | None = None,
    network: points.Network | None = None,
) -> RouteResult | RouteError:
    """`route_points` are the labels of the map points crossed in order;
    `rate_texts` maps a currency to the rate typed for it (units per 1 EUR)."""
    network = network or points.build_network(points.build_catalog(table))
    try:
        route = points.route_crossing_points(network, begin, route_points)
    except points.RouteNotPossible as error:
        return RouteError(str(error))
    if not route:
        return RouteError(FIRST_POINT_MESSAGE)
    if start is None or end is None:
        return RouteError("The period is invalid: enter a valid start date and end date.")
    if end < start:
        return RouteError("The period is invalid: the end date is before the start date.")

    groups = group_by_tso(route)
    rate_texts = rate_texts or {}
    rates: dict[str, Fraction | None] = {}
    invalid: list[str] = []
    for tso, _ in groups:
        currency = TSO_FORMATS[tso][0]
        if currency != EUR and currency not in rates:
            rates[currency], message = parse_fx_rate(rate_texts.get(currency), currency)
            if message:
                invalid.append(currency)

    legs = []
    for tso, tso_points in groups:
        try:
            plan = optimize(start, end, TsoOracle(table, tso_points))
            point_costs = tuple(
                sum((segment_price(TsoOracle(table, [point]), seg) for seg in plan.segments), Fraction(0))
                for point in tso_points
            )
        except NoTariffError as error:
            return RouteError(error.message)
        longest = max((seg.product for seg in plan.segments), key=PRODUCTS.index)
        comparison = None
        if longest != DAILY:
            shorter = PRODUCTS[PRODUCTS.index(longest) - 1]
            comparison = optimize(start, end, TsoOracle(table, tso_points), longest=shorter)
        rate = rates.get(TSO_FORMATS[tso][0])
        legs.append(TsoLeg(tso, tuple(tso_points), plan, rate, point_costs, comparison))

    return RouteResult(
        begin, points.route_end(network, begin, route_points), points.route_text(network, begin, route_points),
        tuple(route), tuple(legs), tuple(rates.items()), tuple(invalid),
    )
