"""Route calculation through real tariff tables: per-TSO pricing, the
1 October boundary, validation messages, and the per-MWh and FX arithmetic."""

from datetime import date
from fractions import Fraction

import pytest

from core import money, points
from core.optimizer import DAILY, MONTHLY, QUARTERLY, Plan
from core.points import BULGARTRANSGAZ, FGSZ, GASTRANS
from core.route import RouteError, RouteResult, TsoLeg, TsoOracle, calculate_route, parse_fx_rate

from .helpers import make_row, make_table

FORMATS = {FGSZ: {}, GASTRANS: {"currency": "EUR"}, BULGARTRANSGAZ: {"currency": "EUR", "unit": "kWh/d"}}


def route_table(begin="BG", end="HU", prices=None, **row_args):
    """One row per point of the route; `prices` maps a TSO to its price overrides."""
    prices = prices or {}
    return make_table(*[
        make_row(eic=p.eic, direction=p.direction, operator=p.tso, prices=prices.get(p.tso), **FORMATS[p.tso], **row_args)
        for p in points.route_points(begin, end)
    ])


def leg(result, tso):
    return next(l for l in result.legs if l.tso == tso)


def products(result, tso):
    return [s.product for s in leg(result, tso).plan.segments]


# --- 3.1 per-TSO price ------------------------------------------------------------------------

def test_summing_entry_and_exit():
    # Gastrans December 2026 on BG -> HU: 1.36 at the Kireevo entry + 2.34 at the Kiskundorozsma 2 exit.
    gastrans = [p for p in points.route_points("BG", "HU") if p.tso == GASTRANS]
    table = make_table(
        make_row(eic=gastrans[0].eic, direction="Entry", operator=GASTRANS, currency="EUR",
                 valid_from="2026-10-01", valid_to=None, prices={"M_Dec": 1.36, "D_Dec": 0.1, "Q4_Oct": 3.76}),
        make_row(eic=gastrans[1].eic, direction="Exit", operator=GASTRANS, currency="EUR",
                 valid_from="2026-10-01", valid_to=None, prices={"M_Dec": 2.34, "D_Dec": 0.2, "Q4_Oct": 6.42}),
    )
    oracle = TsoOracle(table, gastrans)
    assert oracle.month_price(2026, 12) == Fraction("3.70")
    assert oracle.day_price(date(2026, 12, 5)) == Fraction("0.3")
    assert oracle.quarter_price(2026, 4) == Fraction("10.18")
    assert oracle.tariff_used(date(2026, 12, 1), date(2026, 12, 1)) == (
        "entry from 2026-10-01 (open-ended); exit from 2026-10-01 (open-ended)"
    )


def test_a_tso_with_one_point_is_priced_alone_in_its_own_unit():
    table = route_table(prices={BULGARTRANSGAZ: {"M_Dec": 0.11}, FGSZ: {"M_Dec": 93.0}},  # both below 31 x 4 daily
                        valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 12, 1), date(2026, 12, 31))
    assert [(l.tso, len(l.points), l.currency, l.unit) for l in result.legs] == [
        (BULGARTRANSGAZ, 1, "EUR", "kWh/d"), (GASTRANS, 2, "EUR", "kWh/h"), (FGSZ, 1, "HUF", "kWh/h"),
    ]
    assert leg(result, BULGARTRANSGAZ).plan.total == Fraction("0.11")
    assert leg(result, GASTRANS).plan.total == 200  # 100 + 100
    assert leg(result, FGSZ).plan.total == 93


# --- 3.2 validity -------------------------------------------------------------------------------

@pytest.mark.parametrize("country", ["HU", "RS", "BG"])
def test_same_country_is_not_possible(country):
    result = calculate_route(route_table(), country, country, date(2026, 1, 1), date(2026, 1, 5))
    assert isinstance(result, RouteError) and "not possible" in result.message


def test_end_before_start_is_a_message():
    result = calculate_route(route_table(), "BG", "HU", date(2026, 1, 10), date(2026, 1, 9))
    assert isinstance(result, RouteError) and "invalid" in result.message


@pytest.mark.parametrize("start,end", [(None, date(2026, 1, 9)), (date(2026, 1, 9), None), (None, None)])
def test_blank_dates_are_a_message(start, end):
    result = calculate_route(route_table(), "BG", "HU", start, end)
    assert isinstance(result, RouteError) and "invalid" in result.message


def test_no_tariff_for_the_dates_names_the_tso_and_point():
    table = route_table(valid_from="2026-01-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2025, 12, 1), date(2026, 1, 15))
    assert isinstance(result, RouteError)
    assert result.message == "No tariff exists for Bulgartransgaz Kireevo/Zaychar (BG>RS) on 2025-12-01."


def test_missing_rows_of_a_later_point_name_that_point():
    table = make_table(*[
        make_row(eic=p.eic, direction=p.direction, operator=p.tso, **FORMATS[p.tso])
        for p in points.route_points("BG", "HU") if p.tso != FGSZ
    ])
    result = calculate_route(table, "BG", "HU", date(2026, 1, 1), date(2026, 1, 5))
    assert isinstance(result, RouteError) and "FGSZ Kiskundorozsma 2 (RS>HU)" in result.message


# --- optimiser per TSO through real rows -------------------------------------------------------

def test_full_month_is_booked_monthly_through_real_rows():
    table = route_table(valid_from="2026-10-01", valid_to=None)  # every TSO: M 100, D 4 per point
    result = calculate_route(table, "BG", "HU", date(2026, 11, 15), date(2027, 1, 15))
    assert isinstance(result, RouteResult)
    assert products(result, FGSZ) == [DAILY, MONTHLY, DAILY]


def test_tsos_choose_independently():
    months = {"M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0}
    table = route_table(prices={
        GASTRANS: {"Q4_Oct": 140.0, **months},   # per point: 140 < 150, so the quarter
        FGSZ: {"Q4_Oct": 160.0, **months},       # 160 > 150, so three months
        BULGARTRANSGAZ: months,
    }, valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2026, 12, 31))
    assert products(result, GASTRANS) == [QUARTERLY]
    assert products(result, FGSZ) == [MONTHLY] * 3


@pytest.mark.parametrize("q4,expected", [(149.0, [QUARTERLY]), (151.0, [MONTHLY] * 3)])
def test_quarter_flips_with_the_prices_through_real_rows(q4, expected):
    table = route_table("RS", "HU", prices={FGSZ: {"Q4_Oct": q4, "M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0}},
                        valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "RS", "HU", date(2026, 10, 1), date(2026, 12, 31))
    assert products(result, FGSZ) == expected


def test_fx_rate_does_not_change_the_choice():
    table = route_table(valid_from="2026-10-01", valid_to=None)
    shapes = {
        rate: [(l.tso, s.start, s.end, s.product, s.price)
               for l in calculate_route(table, "BG", "HU", date(2026, 11, 15), date(2027, 1, 15), rate).legs
               for s in l.plan.segments]
        for rate in ("", "380", "420", "99999")
    }
    assert len({tuple(v) for v in shapes.values()}) == 1


# --- gas-year boundary ----------------------------------------------------------------------------

def test_period_crossing_1_october_splits_at_the_boundary_with_old_and_new_rows():
    route = points.route_points("RS", "HU")
    table = make_table(*[
        make_row(eic=p.eic, direction=p.direction, operator=p.tso, **FORMATS[p.tso], valid_from=vf, valid_to=vt, prices=pr)
        for p in route
        for vf, vt, pr in (("2025-10-01", "2026-09-30", {"D_Sep": 5.0}),
                           ("2026-10-01", None, {"D_Oct": 20.0, "M_Oct": 1000.0}))
    ])  # 11 September days (55) beat the monthly 100, and October's monthly price is dear
    result = calculate_route(table, "RS", "HU", date(2026, 9, 20), date(2026, 10, 10))
    old, new = leg(result, FGSZ).plan.segments
    assert [(s.start, s.end, s.product) for s in (old, new)] == [
        (date(2026, 9, 20), date(2026, 9, 30), DAILY), (date(2026, 10, 1), date(2026, 10, 10), DAILY),
    ]
    assert old.price == 11 * 5 and new.price == 10 * 20
    assert old.tariff_used == "entry from 2025-10-01"
    assert new.tariff_used == "entry from 2026-10-01 (open-ended)"


# --- over-booking ------------------------------------------------------------------------------------

def test_quarter_minus_its_edge_days_books_the_whole_quarter_when_cheaper():
    table = route_table(valid_from="2026-10-01", valid_to=None)  # per point: Q 300, M 100, D 4
    result = calculate_route(table, "BG", "HU", date(2026, 10, 2), date(2026, 12, 30))
    for l in result.legs:
        assert [(s.start, s.end, s.product) for s in l.plan.segments] == [(date(2026, 10, 1), date(2026, 12, 31), QUARTERLY)]
        assert l.plan.days_outside == 2
    assert result.days == 90


def test_over_booking_product_without_a_tariff_on_its_first_day_is_skipped():
    table = route_table(valid_from="2026-10-15", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 10, 15), date(2026, 11, 30))
    assert isinstance(result, RouteResult)
    assert [(s.start, s.end, s.product) for s in leg(result, FGSZ).plan.segments] == [
        (date(2026, 10, 15), date(2026, 10, 31), DAILY),
        (date(2026, 11, 1), date(2026, 11, 30), MONTHLY),
    ]


# --- 3.3 per-MWh, EUR and route totals -------------------------------------------------------------

def make_leg(tso, total, start=date(2026, 12, 5), end=date(2027, 1, 15), fx=None, all_daily=None):
    plan = Plan(start, end, (), Fraction(total), Fraction(all_daily if all_daily is not None else total))
    return TsoLeg(tso, (), plan, fx)


def test_forty_two_day_period():
    fgsz = make_leg(FGSZ, "2145.47")
    assert fgsz.plan.days == 42
    assert money.format_decimal(fgsz.per_mwh, 4) == "2128.4425"


def test_bulgartransgaz_per_kwh_d_has_no_division_by_24():
    bg = make_leg(BULGARTRANSGAZ, "0.981251", date(2026, 10, 1), date(2027, 9, 30))
    assert bg.plan.days == 365
    assert money.format_decimal(bg.per_mwh, 4) == "2.6884"
    assert bg.eur_per_mwh == bg.per_mwh  # already EUR


def test_exact_2128_4_huf_per_mwh_is_5_3210_eur_at_rate_400():
    fgsz = make_leg(FGSZ, "2145.4272", fx=Fraction(400))  # 2145.4272 / 1008 x 1000 = 2128.4 exactly
    assert fgsz.per_mwh == Fraction("2128.4")
    assert money.format_decimal(fgsz.eur_per_mwh, 4) == "5.3210"


def test_route_total_is_the_sum_of_the_tsos_eur_per_mwh():
    days = (date(2026, 12, 1), date(2026, 12, 10))  # 10 days
    legs = (
        make_leg(BULGARTRANSGAZ, "0.02", *days),        # 0.02 / 10 x 1000 = 2 EUR/MWh
        make_leg(GASTRANS, "0.72", *days),              # 0.72 / 240 x 1000 = 3 EUR/MWh
        make_leg(FGSZ, "480", *days, fx=Fraction(400)),  # 480 / 240 x 1000 = 2000 HUF/MWh = 5 EUR/MWh
    )
    result = RouteResult("BG", "HU", (), legs, Fraction(400), None)
    assert money.format_decimal(result.eur_per_mwh, 4) == "10.0000"


def test_without_a_rate_the_huf_leg_and_route_have_no_eur_figure():
    days = (date(2026, 12, 1), date(2026, 12, 10))
    legs = (make_leg(GASTRANS, "0.72", *days), make_leg(FGSZ, "480", *days))
    result = RouteResult("RS", "HU", (), legs, None, None)
    assert legs[0].eur_per_mwh == 3 and legs[1].eur_per_mwh is None and legs[1].per_mwh == 2000
    assert result.eur_per_mwh is None and result.all_daily_eur_per_mwh is None and result.saving_eur_per_mwh is None


def test_totals_baseline_and_saving_through_the_route():
    table = route_table(valid_from="2026-10-01", valid_to=None)  # per point: M 100, D 4
    result = calculate_route(table, "BG", "HU", date(2026, 12, 1), date(2026, 12, 31), "400")
    fgsz, gastrans = leg(result, FGSZ), leg(result, GASTRANS)
    assert gastrans.plan.total == 200 and gastrans.plan.all_daily_total == 31 * 8 and gastrans.plan.saving == 48
    assert fgsz.eur_per_mwh == Fraction(100) / (24 * 31) * 1000 / 400
    assert result.eur_per_mwh == sum(l.eur_per_mwh for l in result.legs)
    assert result.saving_eur_per_mwh == result.all_daily_eur_per_mwh - result.eur_per_mwh


def test_over_booked_days_are_not_counted():
    table = route_table(valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "RS", "HU", date(2026, 10, 2), date(2026, 12, 30), "400")
    gastrans = leg(result, GASTRANS)
    assert gastrans.plan.days_outside == 2
    assert gastrans.per_mwh == gastrans.plan.total / (24 * 90) * 1000


# --- FX box --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("text,rate,has_message", [
    ("", None, False), ("   ", None, False), (None, None, False),
    ("400", Fraction(400), False), ("395,5", Fraction("395.5"), False), (" 400.25 ", Fraction("400.25"), False),
    ("0", None, True), ("-3", None, True), ("abc", None, True), ("1/2", None, True), ("nan", None, True),
])
def test_fx_rate_parsing(text, rate, has_message):
    parsed, message = parse_fx_rate(text)
    assert parsed == rate
    assert (message is not None) == has_message


def test_route_without_hu_needs_no_rate():
    table = route_table("BG", "RS", valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "RS", date(2026, 12, 1), date(2026, 12, 31), "abc")
    assert not result.needs_fx and result.fx_message is None
    assert result.eur_per_mwh is not None


def test_invalid_rate_keeps_the_own_currency_figures_and_carries_a_message():
    table = route_table(valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 12, 1), date(2026, 12, 3), "abc")
    assert isinstance(result, RouteResult) and result.needs_fx
    assert result.eur_per_mwh is None and "positive number" in result.fx_message
    assert leg(result, FGSZ).per_mwh > 0 and leg(result, GASTRANS).eur_per_mwh is not None
