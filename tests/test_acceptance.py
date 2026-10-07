"""Acceptance tests: the README's "how we would know it works" checks and the
extra ones added since, run through the public `core` API on corridor routes."""

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


def point(tso, name, flow):
    return next(p for p in points.POINTS if (p.tso, p.name, p.flow) == (tso, name, flow))


def leg(result, tso):
    return next(l for l in result.legs if l.tso == tso)


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
        assert isinstance(result, fee.FeeResult), (p, instrument, result)
        assert sum(line.amount for line in result.invoice) == result.total
        checked += 1
    assert checked == 30 * 5


# 2. Given a route that is not possible, it shows a message instead of crashing.
def test_every_country_pair_returns_a_result_or_a_message(sample):
    results = {
        (a, b): calculate_route(sample, a, b, date(2026, 10, 1), date(2027, 3, 31), "400")
        for a, b in product(points.COUNTRIES, repeat=2)
    }
    impossible = {k for k, v in results.items() if isinstance(v, RouteError)}
    assert impossible == {("HU", "HU"), ("RS", "RS"), ("BG", "BG")}
    assert all("not possible" in results[k].message for k in impossible)
    assert all(isinstance(v, RouteResult) for k, v in results.items() if k not in impossible)


def test_impossible_requests_are_messages_not_exceptions(sample):
    for args in [
        ("BG", "HU", date(2026, 12, 31), date(2026, 12, 1)),   # end before start
        ("BG", "HU", None, date(2026, 12, 1)),                 # blank date
        ("BG", "HU", date(2025, 12, 1), date(2026, 1, 5)),     # before the Bulgartransgaz EUR rows
        ("HU", "RS", date(2001, 1, 1), date(2001, 1, 5)),      # before any tariff
        ("RS", "RS", date(2026, 12, 1), date(2026, 12, 5)),    # same country
    ]:
        result = calculate_route(sample, *args)
        assert isinstance(result, RouteError) and result.message


# 3. Given a booking that crosses 1 October, old tariff up to 30 September, new one from 1 October.
def test_period_crossing_the_gas_year_boundary_uses_old_then_new_tariff(sample):
    result = calculate_route(sample, "BG", "HU", date(2026, 9, 20), date(2026, 10, 10), "400")
    for l in result.legs:
        old, new = l.plan.segments
        assert (old.start, old.end, new.start, new.end) == (
            date(2026, 9, 20), date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 10))
        assert "from 2026-10-01" not in old.tariff_used
        assert new.tariff_used.count("from 2026-10-01 (open-ended)") == len(l.points)
        old_rows = [sample.find_row(*p.key, date(2026, 9, 30)) for p in l.points]
        new_rows = [sample.find_row(*p.key, date(2026, 10, 1)) for p in l.points]
        assert old.price == 11 * sum(r.day_price(9) for r in old_rows)
        assert new.price == 10 * sum(r.day_price(10) for r in new_rows)


# 4. Open-ended rows apply to later dates.
def test_open_ended_row_prices_dates_years_after_it_starts(sample):
    result = calculate_route(sample, "BG", "HU", date(2035, 3, 1), date(2035, 3, 31), "400")
    assert isinstance(result, RouteResult)
    for l in result.legs:
        assert l.plan.segments[0].product == MONTHLY
        assert "from 2026-10-01 (open-ended)" in l.plan.segments[0].tariff_used
    start, end = fee.resolve_period(fee.GAS_YEAR, gas_year=2035)
    for p in points.POINTS:
        assert isinstance(fee.calculate_fee(sample, p, fee.GAS_YEAR, start, end, "50000"), fee.FeeResult), p


# 5. The quarter-versus-three-months choice flips when the prices are swapped.
def test_quarter_versus_three_months_flips_with_the_prices():
    formats = {"FGSZ": {}, "Gastran": {"currency": "EUR"}, "BGTRGAZ": {"currency": "EUR", "unit": "kWh/d"}}

    def products(quarter_price):
        prices = {"Q4_Oct": quarter_price / 2, "M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0}  # Gastrans months = 300
        table = make_table(*[
            make_row(eic=p.eic, direction=p.direction, operator=p.tso, valid_from="2026-10-01", valid_to=None,
                     prices=prices, **formats[p.tso])
            for p in points.route_points("BG", "HU")
        ])
        result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2026, 12, 31))
        return [s.product for s in leg(result, "Gastran").plan.segments]

    assert products(250) == [QUARTERLY]
    assert products(350) == [MONTHLY] * 3


# README demo (synthetic sample): guards the numbers quoted in README.md section 1.
def test_readme_demo_figures(sample):
    route = calculate_route(sample, "BG", "HU", date(2026, 10, 1), date(2027, 3, 31), "400")
    fmt = lambda value: money.format_decimal(value, 4)
    assert [p.cleaned_name for p in route.points] == [
        "Kireevo/Zaychar (BG>RS)", "Kireevo/Zaychar (BG>RS)", "Kiskundorozsma 2 (RS>HU)", "Kiskundorozsma 2 (RS>HU)",
    ]
    bg, gastrans, fgsz = route.legs
    assert [s.product for s in bg.plan.segments] == ["quarterly", "quarterly"]
    assert [s.product for s in gastrans.plan.segments] == ["quarterly", "monthly", "monthly", "monthly"]
    assert [s.product for s in fgsz.plan.segments] == ["quarterly", "quarterly"]
    assert (fmt(bg.plan.total), fmt(bg.eur_per_mwh)) == ("0.5253", "2.8863")
    assert (fmt(gastrans.plan.total), fmt(gastrans.eur_per_mwh)) == ("19.3900", "4.4391")
    assert (fmt(fgsz.plan.total), fmt(fgsz.per_mwh), fmt(fgsz.eur_per_mwh)) == ("1519.2871", "347.8221", "0.8696")
    assert fmt(route.eur_per_mwh) == "8.1949"
    assert fmt(route.all_daily_eur_per_mwh) == "14.0247"
    assert fmt(route.saving_eur_per_mwh) == "5.8297"

    over = calculate_route(sample, "BG", "HU", date(2026, 10, 2), date(2026, 12, 30), "400")
    assert all(l.plan.days_outside == 2 for l in over.legs)

    start, end = fee.resolve_period(fee.QUARTER, year=2026, quarter=4)
    result = fee.calculate_fee(sample, point("FGSZ", "Kiskundorozsma 2", "RS>HU"), fee.QUARTER, start, end, "50000")
    assert money.format_decimal(result.capacity, 2) == "2083.33"
    assert result.total == 1_565_115
    assert [line.amount for line in result.invoice] == [527_376, 510_363, 527_376]
    bg_fee = fee.calculate_fee(sample, point("BGTRGAZ", "Kireevo/Zaychar", "BG>RS"), fee.QUARTER, start, end, "50000")
    assert money.format_amount(bg_fee.total, "EUR") == "12,110.87"
    assert [money.format_amount(line.amount, "EUR") for line in bg_fee.invoice] == ["4,080.84", "3,949.20", "4,080.83"]
