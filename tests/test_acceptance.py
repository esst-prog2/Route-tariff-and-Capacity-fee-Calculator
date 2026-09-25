"""Acceptance tests: the README's "how we would know it works" checks and the
extra ones added for this change, run through the public `core` API."""

from datetime import date
from itertools import product

import pytest

from core import fee, money, points
from core.optimizer import MONTHLY, QUARTERLY
from core.route import RouteError, RouteResult, calculate_route
from core.tariffs import load_tariffs, resolve_tariff_path

from .helpers import make_row, make_table


@pytest.fixture(scope="module")
def sample():
    result = load_tariffs(resolve_tariff_path({}))
    assert result.ok and not result.warnings
    return result.table


def point(name, direction):
    return next(p for p in points.POINTS if p.name == name and p.direction == direction)


# 1. Given a quarterly period, the monthly breakdown sums exactly to the total.
@pytest.mark.parametrize("capacity", ["1", "50000", "123456.789"])
def test_monthly_breakdown_sums_to_the_exact_total_for_every_point_and_instrument(sample, capacity):
    checked = 0
    for p, (instrument, selection) in product(points.POINTS, [
        (fee.GAS_YEAR, {"gas_year": 2026}),
        (fee.QUARTER, {"year": 2026, "quarter": 4}),
        (fee.QUARTER, {"year": 2027, "quarter": 1}),
        (fee.MONTH, {"year": 2026, "month": 12}),
        (fee.DAY, {"day": date(2026, 12, 5)}),
    ]):
        start, end = fee.resolve_period(instrument, **selection)
        result = fee.calculate_fee(sample, p, instrument, start, end, capacity)
        assert isinstance(result, fee.FeeResult), (p.cleaned_name, instrument, result)
        assert sum(line.amount for line in result.invoice) == result.total
        checked += 1
    assert checked == 12 * 5


# 2. Given a route that is not possible, it shows a message instead of crashing.
def test_every_entry_exit_combination_returns_a_result_or_a_message(sample):
    results = {
        (e.cleaned_name, x.cleaned_name): calculate_route(sample, e, x, date(2026, 10, 1), date(2027, 3, 31))
        for e, x in product(points.entries(), points.exits())
    }
    assert len(results) == 35
    impossible = {k for k, v in results.items() if isinstance(v, RouteError)}
    # Same physical point (same EIC) in both directions: Csanadpalota, Dravaszerdahely, Balassagyarmat, VIP Bereg
    assert len(impossible) == 4
    assert all(a.split(" (")[0] == b.split(" (")[0] for a, b in impossible)
    assert all(isinstance(v, RouteResult) for k, v in results.items() if k not in impossible)


def test_impossible_requests_are_messages_not_exceptions(sample):
    entry, exit_ = point("Mosonmagyaróvár", "Entry"), point("Kiskundorozsma", "Exit")
    for args in [
        (date(2026, 12, 31), date(2026, 12, 1)),   # end before start
        (None, date(2026, 12, 1)),                 # blank date
        (date(2001, 1, 1), date(2001, 1, 5)),      # before any tariff
    ]:
        result = calculate_route(sample, entry, exit_, *args)
        assert isinstance(result, RouteError) and result.message
    same = calculate_route(sample, point("Csanádpalota", "Entry"), point("Csanádpalota", "Exit"),
                           date(2026, 12, 1), date(2026, 12, 5))
    assert isinstance(same, RouteError) and "not possible" in same.message


# 3. Given a booking that crosses 1 October, old tariff up to 30 September, new one from 1 October.
def test_period_crossing_the_gas_year_boundary_uses_old_then_new_tariff(sample):
    entry, exit_ = point("Mosonmagyaróvár", "Entry"), point("Kiskundorozsma", "Exit")
    result = calculate_route(sample, entry, exit_, date(2026, 9, 20), date(2026, 10, 10))
    old, new = result.plan.segments
    assert (old.start, old.end, new.start, new.end) == (date(2026, 9, 20), date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 10))
    assert "entry from 2025-10-01" in old.tariff_used and "exit from 2025-10-01" in old.tariff_used
    assert "entry from 2026-10-01" in new.tariff_used and "exit from 2026-10-01" in new.tariff_used
    old_row = sample.find_row(entry.eic, "Entry", date(2026, 9, 30)), sample.find_row(exit_.eic, "Exit", date(2026, 9, 30))
    new_row = sample.find_row(entry.eic, "Entry", date(2026, 10, 1)), sample.find_row(exit_.eic, "Exit", date(2026, 10, 1))
    assert old.price == 11 * sum(r.day_price(9) for r in old_row)
    assert new.price == 10 * sum(r.day_price(10) for r in new_row)


# 4. Open-ended rows apply to later dates.
def test_open_ended_row_prices_dates_years_after_it_starts(sample):
    entry, exit_ = point("Mosonmagyaróvár", "Entry"), point("Kiskundorozsma", "Exit")
    result = calculate_route(sample, entry, exit_, date(2035, 3, 1), date(2035, 3, 31))
    assert isinstance(result, RouteResult)
    assert result.plan.segments[0].product == MONTHLY
    assert "from 2026-10-01 (open-ended)" in result.plan.segments[0].tariff_used
    p = point("Kiskundorozsma 2", "Entry")
    start, end = fee.resolve_period(fee.GAS_YEAR, gas_year=2035)
    assert isinstance(fee.calculate_fee(sample, p, fee.GAS_YEAR, start, end, "50000"), fee.FeeResult)


# 5. The quarter-versus-three-months choice flips when the prices are swapped.
def test_quarter_versus_three_months_flips_with_the_prices():
    entry, exit_ = point("Mosonmagyaróvár", "Entry"), point("Kiskundorozsma", "Exit")

    def products(quarter_price):
        half = quarter_price / 2
        prices = {"Q4_Oct": half, "M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0}  # entry + exit months = 300
        table = make_table(
            make_row(eic=entry.eic, direction="Entry", valid_from="2026-10-01", valid_to=None, prices=prices),
            make_row(eic=exit_.eic, direction="Exit", valid_from="2026-10-01", valid_to=None, prices=prices),
        )
        return [s.product for s in calculate_route(table, entry, exit_, date(2026, 10, 1), date(2026, 12, 31)).plan.segments]

    assert products(250) == [QUARTERLY]
    assert products(350) == [MONTHLY] * 3


# README demo (synthetic sample): guards the numbers quoted in README.md section 1.
def test_readme_demo_figures(sample):
    route = calculate_route(sample, point("Mosonmagyaróvár", "Entry"), point("Kiskundorozsma", "Exit"),
                            date(2026, 10, 1), date(2027, 3, 31), "400")
    fmt = lambda value: money.format_decimal(value, 4)
    assert [s.product for s in route.plan.segments] == ["quarterly", "monthly", "monthly", "monthly"]
    assert fmt(route.huf_per_kwh_h) == "4134.1287"
    assert fmt(route.huf_per_mwh) == "946.4580"
    assert fmt(route.eur_per_mwh) == "2.3661"
    assert fmt(route.all_daily_eur_per_mwh) == "4.0796"
    assert fmt(route.plan.saving) == "2993.8050"

    start, end = fee.resolve_period(fee.QUARTER, year=2026, quarter=4)
    result = fee.calculate_fee(sample, point("Kiskundorozsma 2", "Entry"), fee.QUARTER, start, end, "50000")
    assert money.format_decimal(result.capacity_kwh_h, 2) == "2083.33"
    assert result.total == 1_565_115
    assert [line.amount for line in result.invoice] == [527_376, 510_363, 527_376]
