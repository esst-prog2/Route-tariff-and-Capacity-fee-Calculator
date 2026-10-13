"""Route calculation through real tariff tables: per-TSO pricing, the
1 October boundary, validation messages, and the per-MWh and FX arithmetic."""

from datetime import date
from fractions import Fraction
from pathlib import Path

import pytest

from core import money, points
from core.optimizer import DAILY, MONTHLY, QUARTERLY, Plan
from core.points import BULGARTRANSGAZ, FGSZ, GASTRANS
from core.route import (
    RouteError, RouteResult, TsoLeg, TsoOracle, calculate_route, parse_fx_rate, point_tariff, point_tariff_used,
)
from core.tariffs import load_tariffs

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


# --- per-point figures (tab1-eur-per-point) ------------------------------------------------------

@pytest.mark.parametrize("begin,end", [("BG", "HU"), ("HU", "BG"), ("RS", "HU"), ("BG", "RS")])
@pytest.mark.parametrize("start,stop", [
    (date(2026, 10, 1), date(2027, 3, 31)), (date(2026, 10, 2), date(2026, 12, 30)),
    (date(2026, 12, 5), date(2027, 1, 15)), (date(2026, 10, 1), date(2027, 9, 30)),
])
def test_point_costs_add_up_exactly_to_the_leg_and_the_route(begin, end, start, stop):
    table = route_table(begin, end, prices={GASTRANS: {"M_Dec": 130.0, "Q1_Jan": 260.0}},
                        valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, begin, end, start, stop, "400")
    for l in result.legs:
        assert len(l.point_costs) == len(l.points) and sum(l.point_costs) == l.plan.total
    assert sum(x for l in result.legs for x in l.point_eur_per_mwh) == result.eur_per_mwh


def test_each_point_is_costed_with_its_own_prices_for_the_shared_products():
    entry, exit_ = [p for p in points.route_points("BG", "HU") if p.tso == GASTRANS]
    table = make_table(*[
        make_row(eic=p.eic, direction=p.direction, operator=p.tso, prices=prices, **FORMATS[p.tso],
                 valid_from="2026-10-01", valid_to=None)
        for p, prices in [(p, {}) for p in points.route_points("BG", "HU") if p.tso != GASTRANS]
        + [(entry, {"Q4_Oct": 100.0}), (exit_, {"Q4_Oct": 150.0})]
    ])
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2026, 12, 31), "400")
    gastrans = leg(result, GASTRANS)
    assert products(result, GASTRANS) == [QUARTERLY]
    assert gastrans.point_costs == (100, 150)
    assert gastrans.point_eur_per_mwh == (Fraction(100) / (24 * 92) * 1000, Fraction(150) / (24 * 92) * 1000)


def test_without_a_rate_the_fgsz_point_has_no_eur_figure():
    table = route_table(valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2026, 12, 31), "")
    assert leg(result, FGSZ).point_eur_per_mwh == (None,)
    assert None not in leg(result, GASTRANS).point_eur_per_mwh
    assert result.comparison_eur_per_mwh is None and result.comparison_saving_eur_per_mwh is None


# --- next shorter product comparison -----------------------------------------------------------

def test_quarters_are_compared_without_quarterly_products():
    cheap_q4 = {"Q4_Oct": 250.0}  # per point: Q4 250 against three months of 100
    table = route_table(prices={tso: cheap_q4 for tso in FORMATS}, valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2026, 12, 31), "400")
    assert all(products(result, tso) == [QUARTERLY] for tso in (FGSZ, GASTRANS, BULGARTRANSGAZ))
    assert all(l.comparison.total == 300 * len(l.points) for l in result.legs)  # three months of 100
    assert result.comparison_label == "Without quarterly products" and result.comparison_note is None
    assert result.comparison_saving_eur_per_mwh == result.comparison_eur_per_mwh - result.eur_per_mwh > 0


def test_different_longest_products_are_named_per_tso():
    table = route_table(prices={GASTRANS: {"Year": 5000.0}, BULGARTRANSGAZ: {"Year": 5000.0}},
                        valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2027, 9, 30), "400")
    assert leg(result, FGSZ).longest_product == "yearly"
    assert leg(result, GASTRANS).longest_product == leg(result, BULGARTRANSGAZ).longest_product == QUARTERLY
    assert {s.product for s in leg(result, FGSZ).comparison.segments} == {QUARTERLY}
    assert result.comparison_label == "Next shorter products"
    assert result.comparison_note == "FGSZ without yearly; Bulgartransgaz, Gastrans without quarterly"


def test_monthly_is_compared_with_daily_only():
    table = route_table(valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 12, 1), date(2026, 12, 31), "400")
    assert all(products(result, tso) == [MONTHLY] for tso in (FGSZ, GASTRANS, BULGARTRANSGAZ))
    assert all({s.product for s in l.comparison.segments} == {DAILY} for l in result.legs)
    assert result.comparison_label == "Without monthly products"


def test_daily_only_has_no_comparison():
    table = route_table(valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, "BG", "HU", date(2026, 12, 1), date(2026, 12, 5), "400")
    assert all(l.comparison is None for l in result.legs)
    assert result.comparison_label is None and result.comparison_eur_per_mwh is None


def test_bg_to_hu_on_the_real_tariffs():
    table = load_tariffs(Path(__file__).resolve().parent.parent / "data" / "real" / "tariffs_real.xlsx").table
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2027, 3, 31), "400")
    fmt = lambda v: money.format_decimal(v, 4)
    assert [fmt(x) for l in result.legs for x in l.point_eur_per_mwh] == ["1.4431", "0.8494", "0.9684", "0.4348"]
    assert [fmt(v) for v in (result.eur_per_mwh, result.comparison_eur_per_mwh,
                             result.comparison_saving_eur_per_mwh)] == ["3.6957", "3.9913", "0.2956"]
    assert result.comparison_label == "Without quarterly products"


def test_exact_tariff_per_point_on_the_real_tariffs():
    table = load_tariffs(Path(__file__).resolve().parent.parent / "data" / "real" / "tariffs_real.xlsx").table
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2027, 3, 31), "400")
    bg, gastrans = leg(result, BULGARTRANSGAZ), leg(result, GASTRANS)
    q4 = bg.plan.segments[0]
    assert money.format_exact(point_tariff(table, bg.points[0], q4)[0]) == "0.1211087"
    assert money.format_exact(point_tariff(table, gastrans.points[0], gastrans.plan.segments[0])[0]) == "1.88"


def test_daily_tariff_is_the_price_of_one_day():
    table = route_table(valid_from="2026-10-01", valid_to=None)  # D 4 per point
    result = calculate_route(table, "BG", "HU", date(2026, 12, 1), date(2026, 12, 5), "400")
    fgsz = leg(result, FGSZ)
    assert point_tariff(table, fgsz.points[0], fgsz.plan.segments[0]) == (4,)


# --- products across tariff changes -------------------------------------------------------------

def calendar_year_route_table(year_prices=(3.97, 4.10)):
    """BG to HU where Bulgartransgaz's tariffs change on 1 January 2027."""
    rows = []
    for p in points.route_points("BG", "HU"):
        if p.tso == BULGARTRANSGAZ:
            rows += [
                make_row(eic=p.eic, direction=p.direction, operator=p.tso, **FORMATS[p.tso],
                         valid_from="2026-01-01", valid_to="2026-12-31", prices={"Year": year_prices[0]}),
                make_row(eic=p.eic, direction=p.direction, operator=p.tso, **FORMATS[p.tso],
                         valid_from="2027-01-01", valid_to=None, prices={"Year": year_prices[1]}),
            ]
        else:
            rows.append(make_row(eic=p.eic, direction=p.direction, operator=p.tso, **FORMATS[p.tso],
                                 valid_from="2026-01-01", valid_to=None))
    return make_table(*rows)


def test_yearly_product_across_a_1_january_tariff_change():
    table = calendar_year_route_table()
    bg = [p for p in points.route_points("BG", "HU") if p.tso == BULGARTRANSGAZ]
    assert TsoOracle(table, bg).year_price(2026) == Fraction("3.97") * 92 / 365 + Fraction("4.10") * 273 / 365


def test_optimiser_compares_the_weighted_yearly_price():
    # Four quarters cost 4 x 300 = 1200. Priced from its first day the year (1000) would win;
    # weighted it costs 1000 x 92/365 + 1400 x 273/365 = 1299.18, so the quarters win.
    table = calendar_year_route_table(year_prices=(1000.0, 1400.0))
    bg_points = [p for p in points.route_points("BG", "HU") if p.tso == BULGARTRANSGAZ]
    assert TsoOracle(table, bg_points).year_price(2026) > 1200
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2027, 9, 30), "400")
    bg = leg(result, BULGARTRANSGAZ)
    assert [seg.product for seg in bg.plan.segments] == ["quarterly"] * 4
    assert bg.plan.total == 1200


def test_product_priced_from_two_rows_in_details():
    table = calendar_year_route_table()
    result = calculate_route(table, "BG", "HU", date(2026, 10, 1), date(2027, 9, 30), "400")
    bg = leg(result, BULGARTRANSGAZ)
    year = bg.plan.segments[0]
    assert year.product == "yearly"
    assert point_tariff(table, bg.points[0], year) == (Fraction("3.97"), Fraction("4.1"))
    assert point_tariff_used(table, bg.points[0], year) == "from 2026-01-01, from 2027-01-01 (open-ended)"
    assert year.tariff_used == "exit from 2026-01-01, from 2027-01-01 (open-ended)"
