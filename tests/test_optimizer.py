"""Optimizer rules, driven by a fake price oracle so each scenario controls
its own prices (no test relies on the sample's price relationships)."""

from datetime import date, timedelta
from fractions import Fraction

from core.optimizer import DAILY, MONTHLY, QUARTERLY, optimize


class FakeOracle:
    def __init__(self, day=4, month=100, quarter=None):
        self._day, self._month, self._quarter = day, month, quarter or {}

    def day_price(self, day):
        return Fraction(self._day)

    def month_price(self, year, month):
        return Fraction(self._month)

    def quarter_price(self, year, quarter):
        return Fraction(self._quarter.get((year, quarter), 10**9))

    def tariff_used(self, first, last):
        return f"{first}..{last}"


def shape(plan):
    return [(s.start, s.end, s.product) for s in plan.segments]


def test_partial_edge_months_are_priced_daily():
    plan = optimize(date(2026, 12, 5), date(2027, 1, 15), FakeOracle(day=4, month=1))
    assert shape(plan) == [
        (date(2026, 12, 5), date(2026, 12, 31), DAILY),
        (date(2027, 1, 1), date(2027, 1, 15), DAILY),
    ]
    assert plan.days == 42
    assert plan.total == 4 * 42
    assert plan.saving == 0  # nothing to optimise: no full month, even though monthly is far cheaper


def test_full_month_between_partials_is_monthly_when_cheaper():
    plan = optimize(date(2026, 11, 15), date(2027, 1, 15), FakeOracle(day=4, month=100))
    assert shape(plan) == [
        (date(2026, 11, 15), date(2026, 11, 30), DAILY),
        (date(2026, 12, 1), date(2026, 12, 31), MONTHLY),
        (date(2027, 1, 1), date(2027, 1, 15), DAILY),
    ]
    assert plan.total == 16 * 4 + 100 + 15 * 4
    assert plan.all_daily_total == 62 * 4
    assert plan.saving == 62 * 4 - plan.total == 24


def test_full_month_is_daily_when_daily_is_cheaper():
    plan = optimize(date(2026, 12, 1), date(2026, 12, 31), FakeOracle(day=3, month=100))  # 93 < 100
    assert shape(plan) == [(date(2026, 12, 1), date(2026, 12, 31), DAILY)]
    assert plan.total == 93


def test_monthly_wins_a_tie_against_daily():
    plan = optimize(date(2026, 12, 1), date(2026, 12, 31), FakeOracle(day=4, month=124))
    assert [s.product for s in plan.segments] == [MONTHLY]


def test_quarter_cheaper_than_three_months():
    oracle = FakeOracle(day=4, month=100, quarter={(2026, 4): 250})
    plan = optimize(date(2026, 10, 1), date(2026, 12, 31), oracle)
    assert shape(plan) == [(date(2026, 10, 1), date(2026, 12, 31), QUARTERLY)]
    assert plan.total == 250


def test_quarter_dearer_than_three_months():
    oracle = FakeOracle(day=4, month=100, quarter={(2026, 4): 350})
    plan = optimize(date(2026, 10, 1), date(2026, 12, 31), oracle)
    assert [s.product for s in plan.segments] == [MONTHLY, MONTHLY, MONTHLY]
    assert plan.total == 300


def test_quarter_choice_flips_when_prices_are_swapped():
    # Same quarterly price (299); only the monthly price moves: 3 x 100 = 300 vs 3 x 99 = 297.
    cheap_q = optimize(date(2026, 10, 1), date(2026, 12, 31), FakeOracle(month=100, quarter={(2026, 4): 299}))
    dear_q = optimize(date(2026, 10, 1), date(2026, 12, 31), FakeOracle(month=99, quarter={(2026, 4): 299}))
    assert [s.product for s in cheap_q.segments] == [QUARTERLY]
    assert [s.product for s in dear_q.segments] == [MONTHLY] * 3


def test_quarter_wins_a_tie_against_three_months():
    plan = optimize(date(2026, 10, 1), date(2026, 12, 31), FakeOracle(month=100, quarter={(2026, 4): 300}))
    assert [s.product for s in plan.segments] == [QUARTERLY]


def test_quarter_is_compared_with_the_months_as_already_optimised():
    # Daily (3/day) beats monthly (100), so the three months cost 93 + 90 + 93 = 276, not 300.
    cheaper = optimize(date(2026, 10, 1), date(2026, 12, 31), FakeOracle(day=3, month=100, quarter={(2026, 4): 270}))
    assert [s.product for s in cheaper.segments] == [QUARTERLY]
    assert cheaper.total == 270

    dearer = optimize(date(2026, 10, 1), date(2026, 12, 31), FakeOracle(day=3, month=100, quarter={(2026, 4): 280}))
    assert [s.product for s in dearer.segments] == [DAILY, DAILY, DAILY]  # 280 > 276 (though < 300)
    assert dearer.total == 276


def test_partial_quarter_never_uses_the_quarterly_product():
    oracle = FakeOracle(day=4, month=100, quarter={(2026, 4): 1})
    plan = optimize(date(2026, 10, 1), date(2026, 12, 30), oracle)  # Dec is partial
    assert QUARTERLY not in [s.product for s in plan.segments]


def test_two_quarters_in_one_period():
    oracle = FakeOracle(day=4, month=100, quarter={(2026, 4): 250, (2027, 1): 250})
    plan = optimize(date(2026, 10, 1), date(2027, 3, 31), oracle)
    assert shape(plan) == [
        (date(2026, 10, 1), date(2026, 12, 31), QUARTERLY),
        (date(2027, 1, 1), date(2027, 3, 31), QUARTERLY),
    ]
    assert plan.total == 500


def test_single_day():
    plan = optimize(date(2026, 12, 5), date(2026, 12, 5), FakeOracle())
    assert shape(plan) == [(date(2026, 12, 5), date(2026, 12, 5), DAILY)]
    assert plan.days == 1 and plan.total == 4


def test_leap_february_is_a_full_29_day_month():
    plan = optimize(date(2028, 2, 1), date(2028, 2, 29), FakeOracle(day=4, month=100))
    assert [s.product for s in plan.segments] == [MONTHLY]
    assert plan.all_daily_total == 29 * 4


def test_segments_add_up_to_the_total():
    plan = optimize(date(2026, 9, 3), date(2027, 8, 17), FakeOracle(day=4, month=100, quarter={(2026, 4): 250}))
    assert sum(s.price for s in plan.segments) == plan.total
    assert plan.segments[0].start == plan.start and plan.segments[-1].end == plan.end
    for before, after in zip(plan.segments, plan.segments[1:]):
        assert after.start == before.end + timedelta(days=1)
