"""Product labels for tab 1: the products a plan books, named as a trader
books them ("Q4 2026", "GY 2026/27", "Nov 2026 - Feb 2027 (monthly)",
"daily 01-15 Jan 2027"), with the days booked outside the period."""

from __future__ import annotations

from . import periods
from .optimizer import MONTHLY, QUARTERLY, YEARLY, Plan, Segment

MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _month(segment: Segment) -> str:
    return f"{MONTH_NAMES[segment.start.month - 1]} {segment.start.year}"


def _outside(days: int) -> str:
    return f"+{days} day" if days == 1 else f"+{days} days"


def _single(segment: Segment, days_outside: int) -> str:
    first = segment.start
    if segment.product == YEARLY:
        text = f"GY {periods.gas_year_label(periods.gas_year_start_year(first))}"
    elif segment.product == QUARTERLY:
        text = f"Q{periods.quarter_of_month(first.month)} {first.year}"
    elif segment.product == MONTHLY:
        text = _month(segment)
    elif segment.start == segment.end:
        text = f"daily {first.day:02d} {_month(segment)}"
    else:
        text = f"daily {first.day:02d}-{segment.end.day:02d} {_month(segment)}"
    return f"{text} ({_outside(days_outside)})" if days_outside else text


def _runs(segments: tuple[Segment, ...]) -> list[list[Segment]]:
    """Consecutive monthly products form one run; every other product is a run of its own."""
    runs: list[list[Segment]] = []
    for segment in segments:
        previous = runs[-1][-1] if runs else None
        if (segment.product == MONTHLY and previous is not None and previous.product == MONTHLY
                and (segment.start - previous.end).days == 1):
            runs[-1].append(segment)
        else:
            runs.append([segment])
    return runs


def products_text(plan: Plan) -> str:
    parts = []
    for run in _runs(plan.segments):
        outside = sum(s.days_outside(plan.start, plan.end) for s in run)
        if len(run) == 1:
            parts.append(_single(run[0], outside))
        else:
            detail = f"monthly, {_outside(outside)}" if outside else "monthly"
            parts.append(f"{_month(run[0])} - {_month(run[-1])} ({detail})")
    return ", ".join(parts)
