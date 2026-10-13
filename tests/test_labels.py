"""Product labels in the tab 1 point table (Product labels requirement)."""

from datetime import date
from fractions import Fraction

import pytest

from core.labels import products_text
from core.optimizer import DAILY, MONTHLY, QUARTERLY, YEARLY, Plan, Segment


def plan(start, end, *segments):
    segs = tuple(Segment(first, last, product, Fraction(1), "") for first, last, product in segments)
    return Plan(start, end, segs, Fraction(len(segs)), Fraction(0))


@pytest.mark.parametrize("p,text", [
    (plan(date(2026, 10, 1), date(2027, 3, 31),
          (date(2026, 10, 1), date(2026, 12, 31), QUARTERLY), (date(2027, 1, 1), date(2027, 3, 31), QUARTERLY)),
     "Q4 2026, Q1 2027"),
    (plan(date(2026, 10, 1), date(2027, 9, 30), (date(2026, 10, 1), date(2027, 9, 30), YEARLY)),
     "GY 2026/27"),
    (plan(date(2026, 11, 10), date(2027, 2, 20),
          (date(2026, 11, 1), date(2026, 11, 30), MONTHLY), (date(2026, 12, 1), date(2026, 12, 31), MONTHLY),
          (date(2027, 1, 1), date(2027, 1, 31), MONTHLY), (date(2027, 2, 1), date(2027, 2, 28), MONTHLY)),
     "Nov 2026 - Feb 2027 (monthly, +17 days)"),
    (plan(date(2026, 12, 5), date(2027, 1, 15),
          (date(2026, 12, 1), date(2026, 12, 31), MONTHLY), (date(2027, 1, 1), date(2027, 1, 15), DAILY)),
     "Dec 2026 (+4 days), daily 01-15 Jan 2027"),
    (plan(date(2027, 1, 5), date(2027, 1, 5), (date(2027, 1, 5), date(2027, 1, 5), DAILY)),
     "daily 05 Jan 2027"),
    (plan(date(2026, 10, 2), date(2026, 10, 31), (date(2026, 10, 1), date(2026, 10, 31), MONTHLY)),
     "Oct 2026 (+1 day)"),
    (plan(date(2026, 10, 2), date(2026, 12, 30), (date(2026, 10, 1), date(2026, 12, 31), QUARTERLY)),
     "Q4 2026 (+2 days)"),
    (plan(date(2026, 11, 1), date(2026, 12, 31),
          (date(2026, 11, 1), date(2026, 11, 30), MONTHLY), (date(2026, 12, 1), date(2026, 12, 31), MONTHLY)),
     "Nov 2026 - Dec 2026 (monthly)"),
    (plan(date(2026, 9, 20), date(2026, 10, 10),
          (date(2026, 9, 20), date(2026, 9, 30), DAILY), (date(2026, 10, 1), date(2026, 10, 10), DAILY)),
     "daily 20-30 Sep 2026, daily 01-10 Oct 2026"),
])
def test_products_text(p, text):
    assert products_text(p) == text
