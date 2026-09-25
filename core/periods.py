"""Calendar helpers: gas years, calendar quarters, calendar months and the
tariff column names that belong to them."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterator

# The tariff file uses Hungarian month abbreviations (May is "Maj").
_MONTH_SUFFIX = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Maj", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}
# Calendar quarter number -> tariff column (Q4 = Oct-Dec, Q1 = Jan-Mar, ...).
_QUARTER_COLUMN = {1: "Q1_Jan", 2: "Q2_Apr", 3: "Q3_Jul", 4: "Q4_Oct"}

YEAR_COLUMN = "Year"
MONTH_COLUMNS = [f"M_{_MONTH_SUFFIX[m]}" for m in range(1, 13)]
DAY_COLUMNS = [f"D_{_MONTH_SUFFIX[m]}" for m in range(1, 13)]
QUARTER_COLUMNS = list(_QUARTER_COLUMN.values())
PRICE_COLUMNS = [YEAR_COLUMN, *QUARTER_COLUMNS, *MONTH_COLUMNS, *DAY_COLUMNS]


def month_column(month: int) -> str:
    return f"M_{_MONTH_SUFFIX[month]}"


def day_column(month: int) -> str:
    return f"D_{_MONTH_SUFFIX[month]}"


def quarter_column(quarter: int) -> str:
    return _QUARTER_COLUMN[quarter]


def month_first(year: int, month: int) -> date:
    return date(year, month, 1)


def month_last(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def quarter_of_month(month: int) -> int:
    return (month - 1) // 3 + 1


def quarter_months(year: int, quarter: int) -> list[tuple[int, int]]:
    first = (quarter - 1) * 3 + 1
    return [(year, first + i) for i in range(3)]


def quarter_period(year: int, quarter: int) -> tuple[date, date]:
    months = quarter_months(year, quarter)
    return month_first(*months[0]), month_last(*months[-1])


def gas_year_start_year(day: date) -> int:
    """Calendar year in which the gas year containing `day` starts (1 October)."""
    return day.year if day.month >= 10 else day.year - 1


def gas_year_period(start_year: int) -> tuple[date, date]:
    return date(start_year, 10, 1), date(start_year + 1, 9, 30)


def gas_year_label(start_year: int) -> str:
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def quarter_label(year: int, quarter: int) -> str:
    return f"{year} Q{quarter}"


def days_in_period(start: date, end: date) -> int:
    """Number of calendar days, both dates inclusive."""
    return (end - start).days + 1


def iter_days(start: date, end: date) -> Iterator[date]:
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


@dataclass(frozen=True)
class MonthSlice:
    """The part of a calendar month that lies inside a booking period."""

    year: int
    month: int
    first: date
    last: date
    full: bool  # the whole calendar month is inside the period

    @property
    def days(self) -> int:
        return days_in_period(self.first, self.last)


def month_slices(start: date, end: date) -> list[MonthSlice]:
    """Calendar months touched by [start, end] (inclusive), in order."""
    slices: list[MonthSlice] = []
    year, month = start.year, start.month
    while date(year, month, 1) <= end:
        m_first, m_last = month_first(year, month), month_last(year, month)
        first, last = max(start, m_first), min(end, m_last)
        slices.append(MonthSlice(year, month, first, last, first == m_first and last == m_last))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return slices
