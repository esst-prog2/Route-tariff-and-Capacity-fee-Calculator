"""Cheapest quarterly / monthly / daily booking combination for a period.

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


@dataclass(frozen=True)
class Segment:
    start: date
    end: date
    product: str
    price: Fraction
    tariff_used: str


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
    def saving(self) -> Fraction:
        return self.all_daily_total - self.total


def optimize(start: date, end: date, oracle: PriceOracle) -> Plan:
    """Cheapest cover of [start, end] (inclusive). Ties prefer the coarser
    product: quarter over months over days.

    1. A full calendar month costs min(monthly, sum of its daily prices).
    2. A partly covered month is priced day by day.
    3. A fully covered calendar quarter costs min(quarterly, the sum of its
       three months as priced by 1).
    Each monthly or quarterly product uses the row valid on its first day."""
    slices = periods.month_slices(start, end)

    month_choice: dict[tuple[int, int], tuple[str, Fraction]] = {}
    all_daily_total = Fraction(0)
    for s in slices:
        daily_sum = sum((oracle.day_price(d) for d in periods.iter_days(s.first, s.last)), Fraction(0))
        all_daily_total += daily_sum
        if s.full:
            monthly = oracle.month_price(s.year, s.month)
            month_choice[(s.year, s.month)] = (MONTHLY, monthly) if monthly <= daily_sum else (DAILY, daily_sum)
        else:
            month_choice[(s.year, s.month)] = (DAILY, daily_sum)

    full_months = {(s.year, s.month) for s in slices if s.full}
    quarter_price: dict[tuple[int, int], Fraction] = {}
    for s in slices:
        quarter = periods.quarter_of_month(s.month)
        if (s.year, quarter) in quarter_price:
            continue
        months = periods.quarter_months(s.year, quarter)
        if all(m in full_months for m in months):
            price = oracle.quarter_price(s.year, quarter)
            if price <= sum((month_choice[m][1] for m in months), Fraction(0)):
                quarter_price[(s.year, quarter)] = price

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
        used_last = s.first if product == MONTHLY else s.last
        segments.append(Segment(s.first, s.last, product, price, oracle.tariff_used(s.first, used_last)))

    total = sum((seg.price for seg in segments), Fraction(0))
    return Plan(start, end, tuple(segments), total, all_daily_total)
