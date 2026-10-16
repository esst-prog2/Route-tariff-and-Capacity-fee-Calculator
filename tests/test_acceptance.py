"""Acceptance tests: the README's "how we would know it works" checks and the
extra ones added since, run through the public `core` API on corridor routes."""

from datetime import date
from fractions import Fraction
from itertools import product

import pytest

from core import fee, money, points
from core.optimizer import MONTHLY, QUARTERLY, optimize
from core.route import RouteError, RouteResult, TsoOracle, calculate_route, point_tariff_used
from core.tariffs import DEFAULT_PATH, DEFAULT_SAMPLE_PATH, load_tariffs

from .helpers import KNOWN_POINTS, KISKUNDOROZSMA_2, corridor, corridor_points, make_row, make_table


@pytest.fixture(scope="module")
def sample():
    result = load_tariffs(DEFAULT_SAMPLE_PATH)
    assert result.ok and not result.warnings
    return result.table


def point(tso, name, flow):
    return next(p for p in KNOWN_POINTS if (p.tso, p.name, p.flow) == (tso, name, flow))


def leg(result, tso):
    return next(l for l in result.legs if l.tso == tso)


# 1. Given a quarterly period, the monthly breakdown sums exactly to the total.
@pytest.mark.parametrize("capacity", ["1", "50000", "123456.789"])
def test_monthly_breakdown_sums_to_the_exact_total_for_every_point_and_instrument(sample, capacity):
    checked = 0
    for p, (instrument, selection) in product(KNOWN_POINTS, [
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
def test_every_corridor_route_returns_a_result_and_a_return_trip_a_message(sample):
    pairs = [(a, b) for a, b in product(["HU", "RS", "BG"], repeat=2) if a != b]
    for a, b in pairs:
        result = calculate_route(sample, *corridor(a, b), date(2026, 10, 1), date(2027, 3, 31), {"HUF": "400"})
        assert isinstance(result, RouteResult), (a, b, result)
    back = calculate_route(sample, "HU", [KISKUNDOROZSMA_2, KISKUNDOROZSMA_2], date(2026, 10, 1), date(2027, 3, 31))
    assert isinstance(back, RouteError) and "not possible" in back.message.lower()


def test_impossible_requests_are_messages_not_exceptions(sample):
    for args in [
        (*corridor("BG", "HU"), date(2026, 12, 31), date(2026, 12, 1)),   # end before start
        (*corridor("BG", "HU"), None, date(2026, 12, 1)),                 # blank date
        (*corridor("BG", "HU"), date(2025, 12, 1), date(2026, 1, 5)),     # before the Bulgartransgaz EUR rows
        (*corridor("HU", "RS"), date(2001, 1, 1), date(2001, 1, 5)),      # before any tariff
        ("RS", [KISKUNDOROZSMA_2, KISKUNDOROZSMA_2], date(2026, 12, 1), date(2026, 12, 5)),  # back into RS
        ("BG", ["Vyrava (PL - SK)"], date(2026, 12, 1), date(2026, 12, 5)),  # not on BG's border
        ("HU", [], date(2026, 12, 1), date(2026, 12, 5)),                 # no point yet
    ]:
        result = calculate_route(sample, *args)
        assert isinstance(result, RouteError) and result.message


# 3. Given a booking that crosses 1 October, old tariff up to 30 September, new one from 1 October.
def test_period_crossing_the_gas_year_boundary_uses_old_then_new_tariff(sample):
    result = calculate_route(sample, *corridor("BG", "HU"), date(2026, 9, 20), date(2026, 10, 10), {"HUF": "400"})
    for l in result.legs:
        old, new = l.plan.segments
        assert (old.start, old.end, new.start, new.end) == (
            date(2026, 9, 20), date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 10))
        for p in l.points:
            assert "from 2026-10-01" not in point_tariff_used(sample, p, old)
            assert point_tariff_used(sample, p, new) == "from 2026-10-01 (open-ended)"
        old_rows = [sample.find_row(*p.key, date(2026, 9, 30)) for p in l.points]
        new_rows = [sample.find_row(*p.key, date(2026, 10, 1)) for p in l.points]
        assert old.price == 11 * sum(r.day_price(9) for r in old_rows)
        assert new.price == 10 * sum(r.day_price(10) for r in new_rows)


# 4. Open-ended rows apply to later dates.
def test_open_ended_row_prices_dates_years_after_it_starts(sample):
    result = calculate_route(sample, *corridor("BG", "HU"), date(2035, 3, 1), date(2035, 3, 31), {"HUF": "400"})
    assert isinstance(result, RouteResult)
    for l in result.legs:
        assert l.plan.segments[0].product == MONTHLY
        for p in l.points:
            assert "from 2026-10-01 (open-ended)" in point_tariff_used(sample, p, l.plan.segments[0])
    start, end = fee.resolve_period(fee.GAS_YEAR, gas_year=2035)
    for p in KNOWN_POINTS:
        assert isinstance(fee.calculate_fee(sample, p, fee.GAS_YEAR, start, end, "50000"), fee.FeeResult), p


# 5. The quarter-versus-three-months choice flips when the prices are swapped.
def test_quarter_versus_three_months_flips_with_the_prices():
    formats = {"FGSZ": {}, "Gastran": {"currency": "EUR"}, "BGTRGAZ": {"currency": "EUR", "unit": "kWh/d"}}

    def products(quarter_price):
        prices = {"Q4_Oct": quarter_price / 2, "M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0}  # Gastrans months = 300
        table = make_table(*[
            make_row(eic=p.eic, direction=p.direction, operator=p.tso, name=p.cleaned_name, valid_from="2026-10-01", valid_to=None,
                     prices=prices, **formats[p.tso])
            for p in corridor_points("BG", "HU")
        ])
        result = calculate_route(table, *corridor("BG", "HU"), date(2026, 10, 1), date(2026, 12, 31))
        return [s.product for s in leg(result, "Gastran").plan.segments]

    assert products(250) == [QUARTERLY]
    assert products(350) == [MONTHLY] * 3


# The BG > HU route on the synthetic sample, 2026-10-01 to 2027-03-31 (182 days) at 400 HUF per EUR. The
# expected values are worked out by hand from the sample's cells (rows valid from 2026-10-01, read in Excel),
# not copied from running the code:
#   Bulgartransgaz exit Kireevo/Zaychar, EUR per kWh/d: Q4_Oct 0.2422174, Q1_Jan 0.283084
#   Gastrans entry Kireevo/Zaychar, EUR per kWh/h:  Q4_Oct 3.76, Q1_Jan 3.66, M_Jan 1.36, M_Feb 1.24, M_Mar 1.36
#   Gastrans exit Kiskundorozsma 2, EUR per kWh/h:  Q4_Oct 6.42, Q1_Jan 6.27, M_Jan 1.56, M_Feb 2.13, M_Mar 1.56
#   FGSZ entry Kiskundorozsma 2, HUF per kWh/h:     Q4_Oct 751.255428, Q1_Jan 768.031704
# Gastrans: Q1 as a quarter costs 3.66 + 6.27 = 9.93, as three months 2.92 + 3.37 + 2.92 = 9.21, so it books
# Q4 and the three months. Everyone else books both quarters (no month or day price undercuts them here).
SAMPLE_BG = Fraction("0.2422174") + Fraction("0.283084")                         # 0.5253014 EUR per kWh/d
SAMPLE_GASTRANS = Fraction("3.76") + Fraction("6.42") + Fraction("9.21")          # 19.39 EUR per kWh/h
SAMPLE_FGSZ = Fraction("751.255428") + Fraction("768.031704")                     # 1519.287132 HUF per kWh/h
SAMPLE_EUR_PER_MWH = (SAMPLE_BG / 182 + SAMPLE_GASTRANS / (24 * 182) + SAMPLE_FGSZ / (24 * 182) / 400) * 1000


def test_sample_route_figures_worked_out_by_hand(sample):
    route = calculate_route(sample, *corridor("BG", "HU"), date(2026, 10, 1), date(2027, 3, 31), {"HUF": "400"})
    assert [p.cleaned_name for p in route.points] == [
        "Kireevo/Zaychar (BG>RS)", "Kireevo/Zaychar (BG>RS)", "Kiskundorozsma 2 (RS>HU)", "Kiskundorozsma 2 (RS>HU)",
    ]
    bg, gastrans, fgsz = route.legs
    assert [s.product for s in bg.plan.segments] == ["quarterly", "quarterly"]
    assert [s.product for s in gastrans.plan.segments] == ["quarterly", "monthly", "monthly", "monthly"]
    assert [s.product for s in fgsz.plan.segments] == ["quarterly", "quarterly"]
    assert (bg.plan.total, gastrans.plan.total, fgsz.plan.total) == (SAMPLE_BG, SAMPLE_GASTRANS, SAMPLE_FGSZ)
    assert route.eur_per_mwh == SAMPLE_EUR_PER_MWH
    assert money.format_decimal(route.eur_per_mwh, 4) == "8.1949"

    over = calculate_route(sample, *corridor("BG", "HU"), date(2026, 10, 2), date(2026, 12, 30), {"HUF": "400"})
    assert all(l.plan.days_outside == 2 for l in over.legs)


def test_sample_capacity_fees_worked_out_by_hand(sample):
    start, end = fee.resolve_period(fee.QUARTER, year=2026, quarter=4)
    # 50,000 kWh/d / 24 = 2083.333... kWh/h x 751.255428 HUF = 1,565,115.48 -> 1,565,115 HUF, split 31:30:31 by days.
    result = fee.calculate_fee(sample, point("FGSZ", "Kiskundorozsma 2", "RS>HU"), fee.QUARTER, start, end, "50000")
    assert money.format_decimal(result.capacity, 2) == "2083.33"
    assert result.total == 1_565_115
    assert [line.amount for line in result.invoice] == [527_376, 510_363, 527_376]
    # Per kWh/d, no division by 24: 50,000 x 0.2422174 EUR = 12,110.87 EUR.
    bg_fee = fee.calculate_fee(sample, point("BGTRGAZ", "Kireevo/Zaychar", "BG>RS"), fee.QUARTER, start, end, "50000")
    assert money.format_amount(bg_fee.total, "EUR") == "12,110.87"
    assert sum(line.amount for line in bg_fee.invoice) == bg_fee.total


# README section 1 on the real tariffs. Cells read in Excel from data/real/tariffs_real.xlsx, Q4_Oct of the rows
# valid on every day of 2026 Q4: Bulgartransgaz exit Kireevo/Zaychar 0.1211087 EUR per kWh/d, Gastrans entry
# Kireevo/Zaychar 1.88 and exit Kiskundorozsma 2 2.14 EUR per kWh/h, FGSZ entry Kiskundorozsma 2 375.627714 HUF
# per kWh/h, GAZ-SYSTEM entry Świnoujście 5.6178144 PLN per kWh/h.
@pytest.fixture(scope="module")
def real():
    result = load_tariffs(DEFAULT_PATH)
    assert result.ok
    return result.table


def test_readme_over_booking_route_worked_out_by_hand(real):
    # 2026-10-02 to 2026-12-30 is 90 days; every TSO books the whole Q4, and only the 90 days count as energy:
    # 0.1211087 / 90 x 1000 + (1.88 + 2.14) / (24 x 90) x 1000 + 375.627714 / (24 x 90) x 1000 / 400
    # = 1.345652 + 1.861111 + 0.434754 = 3.641518 EUR/MWh.
    by_hand = (Fraction("0.1211087") / 90 + Fraction("4.02") / (24 * 90) + Fraction("375.627714") / (24 * 90) / 400) * 1000
    route = calculate_route(real, *corridor("BG", "HU"), date(2026, 10, 2), date(2026, 12, 30), {"HUF": "400"})
    assert route.eur_per_mwh == by_hand
    assert money.format_decimal(route.eur_per_mwh, 4) == "3.6415"


def test_readme_lng_entry_worked_out_by_hand(real):
    # 50,000 kWh/d / 24 x 5.6178144 PLN = 280,890.72 / 24 = 11,703.78 PLN exactly.
    swinoujscie = next(p for p in points.build_catalog(real).lng if p.name == "Świnoujście")
    start, end = fee.resolve_period(fee.QUARTER, year=2026, quarter=4)
    result = fee.calculate_fee(real, swinoujscie, fee.QUARTER, start, end, "50,000")
    assert result.exact_total == Fraction("11703.78")
    assert money.format_amount(result.total, "PLN") == "11,703.78"


# Homework 5: a link to reality. The expected value is not computed by the program: the user read the
# two `Year` cells (Firm rows valid from 2026-10-01) in data/sample/tariffs_sample.xlsx by hand in Excel:
# Mosonmagyaróvár AT>HU entry 2447.18 + Kiskundorozsma HU>RS exit 2652.96 = 5100.14 HUF per kWh/h.
YEARLY_PRODUCT_BY_HAND = Fraction("5100.14")


def test_a_whole_gas_year_never_costs_more_than_the_yearly_product(sample):
    # The FGSZ entry-to-exit route is no longer a tab 1 route, so the same two points go to the optimiser directly.
    oracle = TsoOracle(sample, [point("FGSZ", "Mosonmagyaróvár", "AT>HU"), point("FGSZ", "Kiskundorozsma", "HU>RS")])
    plan = optimize(date(2026, 10, 1), date(2027, 9, 30), oracle)
    assert plan.total <= YEARLY_PRODUCT_BY_HAND, (
        f"cheapest plan {float(plan.total):.4f} > yearly product {float(YEARLY_PRODUCT_BY_HAND)}: "
        f"{[s.product for s in plan.segments]}")
