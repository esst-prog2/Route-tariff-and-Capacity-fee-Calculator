"""Cheapest quarterly / monthly / daily booking combination for a period,
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


class PriceOracle(Protocol):
    """Prices in HUF per 1 kWh/h for the whole product period."""

    def day_price(self, day: date) -> Fraction: ...

    def month_price(self, year: int, month: int) -> Fraction: ...

    def quarter_price(self, year: int, quarter: int) -> Fraction: ...

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
    """Cheapest way to cover every day of [start, end] (inclusive). A monthly
    or quarterly product may also cover days outside the period (over-booking)
    when that is cheaper. Ties prefer the coarser product: quarter over months
    over days.

    1. Each calendar month touched costs min(monthly, the daily prices of its
       requested days).
    2. Each calendar quarter touched costs min(quarterly, the sum of its
       touched months as priced by 1).
    Each monthly or quarterly product uses the row valid on its first day; one
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

    segments: list[Segment] = []
    emitted_quarters: set[tuple[int, int]] = set()
    for s in slices:
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
