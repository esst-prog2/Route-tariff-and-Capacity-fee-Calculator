"""Cheapest yearly / quarterly / monthly / daily booking combination for a period,
allowing products to over-book days outside it when that is cheaper.

The optimizer is pure: it asks a `PriceOracle` for prices (already summed for
a route) and never sees currencies or exchange rates, so its choice cannot
depend on an FX rate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Protocol

from . import periods

DAILY = "daily"
MONTHLY = "monthly"
QUARTERLY = "quarterly"
YEARLY = "yearly"


class PriceOracle(Protocol):
    """Prices in HUF per 1 kWh/h for the whole product period."""

    def day_price(self, day: date) -> Fraction: ...

    def month_price(self, year: int, month: int) -> Fraction: ...

    def quarter_price(self, year: int, quarter: int) -> Fraction: ...

    def year_price(self, gas_year: int) -> Fraction:
        """The gas year starting on 1 October of `gas_year`."""
        ...

    def tariff_used(self, first: date, last: date) -> str:
        """Describe the tariff rows behind the prices on days first..last."""
        ...


class PriceUnavailable(Exception):
    """Raised by an oracle when no tariff applies on a product's first day."""


@dataclass(frozen=True)
class Segment:
    start: date
    end: date
    product: str
    price: Fraction
    tariff_used: str

    def days_outside(self, start: date, end: date) -> int:
        """Days this product covers outside the requested period [start, end]."""
        inside = (min(self.end, end) - max(self.start, start)).days + 1
        return periods.days_in_period(self.start, self.end) - max(inside, 0)


@dataclass(frozen=True)
class Plan:
    start: date
    end: date
    segments: tuple[Segment, ...]
    total: Fraction
    all_daily_total: Fraction

    @property
    def days(self) -> int:
        return periods.days_in_period(self.start, self.end)

    @property
    def days_outside(self) -> int:
        """Over-booked days: paid for but outside the requested period."""
        return sum(seg.days_outside(self.start, self.end) for seg in self.segments)

    @property
    def saving(self) -> Fraction:
        return self.all_daily_total - self.total


def optimize(start: date, end: date, oracle: PriceOracle) -> Plan:
    """Cheapest way to cover every day of [start, end] (inclusive). A yearly,
    monthly or quarterly product may also cover days outside the period
    (over-booking) when that is cheaper. Ties prefer the coarser product: gas
    year over quarters over months over days.

    1. Each calendar month touched costs min(monthly, the daily prices of its
       requested days).
    2. Each calendar quarter touched costs min(quarterly, the sum of its
       touched months as priced by 1).
    3. Each gas year (1 October - 30 September) touched costs min(yearly, the
       sum of its touched quarters as priced by 2).
    Each yearly, monthly or quarterly product uses the row valid on its first day; one
    that starts before the period and has no price there is not an option."""
    slices = periods.month_slices(start, end)

    month_choice: dict[tuple[int, int], tuple[str, Fraction]] = {}
    all_daily_total = Fraction(0)
    for s in slices:
        daily_sum = sum((oracle.day_price(d) for d in periods.iter_days(s.first, s.last)), Fraction(0))
        all_daily_total += daily_sum
        monthly = _optional_price(lambda: oracle.month_price(s.year, s.month))
        month_choice[(s.year, s.month)] = (
            (MONTHLY, monthly) if monthly is not None and monthly <= daily_sum else (DAILY, daily_sum)
        )

    quarter_months: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for s in slices:
        quarter_months.setdefault((s.year, periods.quarter_of_month(s.month)), []).append((s.year, s.month))
    quarter_price: dict[tuple[int, int], Fraction] = {}
    for key, months in quarter_months.items():
        price = _optional_price(lambda: oracle.quarter_price(*key))
        if price is not None and price <= sum((month_choice[m][1] for m in months), Fraction(0)):
            quarter_price[key] = price

    def quarter_cost(key: tuple[int, int]) -> Fraction:
        if key in quarter_price:
            return quarter_price[key]
        return sum((month_choice[m][1] for m in quarter_months[key]), Fraction(0))

    year_quarters: dict[int, list[tuple[int, int]]] = {}
    for key in quarter_months:
        year_quarters.setdefault(periods.gas_year_start_year(periods.quarter_period(*key)[0]), []).append(key)
    year_price: dict[int, Fraction] = {}
    for gas_year, quarters in year_quarters.items():
        price = _optional_price(lambda: oracle.year_price(gas_year))
        if price is not None and price <= sum((quarter_cost(q) for q in quarters), Fraction(0)):
            year_price[gas_year] = price

    segments: list[Segment] = []
    emitted_quarters: set[tuple[int, int]] = set()
    emitted_years: set[int] = set()
    for s in slices:
        gas_year = periods.gas_year_start_year(s.first)
        if gas_year in year_price:
            if gas_year not in emitted_years:
                emitted_years.add(gas_year)
                first, last = periods.gas_year_period(gas_year)
                segments.append(Segment(first, last, YEARLY, year_price[gas_year], oracle.tariff_used(first, first)))
            continue
        quarter_key = (s.year, periods.quarter_of_month(s.month))
        if quarter_key in quarter_price:
            if quarter_key not in emitted_quarters:
                emitted_quarters.add(quarter_key)
                first, last = periods.quarter_period(*quarter_key)
                segments.append(
                    Segment(first, last, QUARTERLY, quarter_price[quarter_key], oracle.tariff_used(first, first))
                )
            continue
        product, price = month_choice[(s.year, s.month)]
        if product == MONTHLY:
            first, last = periods.month_first(s.year, s.month), periods.month_last(s.year, s.month)
            segments.append(Segment(first, last, MONTHLY, price, oracle.tariff_used(first, first)))
        else:
            segments.append(Segment(s.first, s.last, DAILY, price, oracle.tariff_used(s.first, s.last)))

    total = sum((seg.price for seg in segments), Fraction(0))
    return Plan(start, end, tuple(segments), total, all_daily_total)


def _optional_price(get_price) -> Fraction | None:
    """The price, or None when no tariff applies on the product's first day."""
    try:
        return get_price()
    except PriceUnavailable:
        return None
