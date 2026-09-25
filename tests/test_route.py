"""Route calculation through real tariff tables: pricing, the 1 October
boundary, validation messages, and the per-MWh and FX arithmetic."""

from datetime import date
from fractions import Fraction

import pytest

from core import money, points
from core.optimizer import DAILY, MONTHLY, QUARTERLY, Plan
from core.route import RouteError, RouteOracle, RouteResult, calculate_route, parse_fx_rate

from .helpers import make_row, make_table

ENTRY = next(p for p in points.entries() if p.name == "Mosonmagyaróvár")
EXIT = next(p for p in points.exits() if p.name == "Kiskundorozsma")


def two_point_table(entry_prices=None, exit_prices=None, **row_args):
    return make_table(
        make_row(eic=ENTRY.eic, direction="Entry", prices=entry_prices, **row_args),
        make_row(eic=EXIT.eic, direction="Exit", prices=exit_prices, **row_args),
    )


# --- 5.1 route price ---------------------------------------------------------------

def test_route_price_is_entry_plus_exit_for_the_same_product():
    table = two_point_table(
        {"M_Dec": 400.0, "D_Dec": 10.0, "Q4_Oct": 900.0},
        {"M_Dec": 300.0, "D_Dec": 7.0, "Q4_Oct": 800.0},
        valid_from="2026-10-01", valid_to=None,
    )
    oracle = RouteOracle(table, ENTRY, EXIT)
    assert oracle.month_price(2026, 12) == 700
    assert oracle.day_price(date(2026, 12, 5)) == 17
    assert oracle.quarter_price(2026, 4) == 1700


def test_tariff_used_lists_entry_and_exit_rows():
    table = two_point_table(valid_from="2026-10-01", valid_to=None)
    text = RouteOracle(table, ENTRY, EXIT).tariff_used(date(2026, 12, 1), date(2026, 12, 1))
    assert text == "entry from 2026-10-01 (open-ended); exit from 2026-10-01 (open-ended)"


# --- 5.2 / 5.3 through the full stack ---------------------------------------------------

def test_full_month_is_booked_monthly_through_real_rows():
    table = two_point_table(
        {"M_Dec": 100.0, "D_Dec": 4.0}, {"M_Dec": 100.0, "D_Dec": 4.0}, valid_from="2026-10-01", valid_to=None
    )
    result = calculate_route(table, ENTRY, EXIT, date(2026, 11, 15), date(2027, 1, 15))
    assert isinstance(result, RouteResult)
    assert [s.product for s in result.plan.segments] == [DAILY, MONTHLY, DAILY]


def test_quarter_flips_with_the_prices_through_real_rows():
    def run(q4_price):
        table = two_point_table(
            {"Q4_Oct": q4_price / 2, "M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0},
            {"Q4_Oct": q4_price / 2, "M_Oct": 50.0, "M_Nov": 50.0, "M_Dec": 50.0},
            valid_from="2026-10-01", valid_to=None,
        )
        return calculate_route(table, ENTRY, EXIT, date(2026, 10, 1), date(2026, 12, 31))

    assert [s.product for s in run(299).plan.segments] == [QUARTERLY]  # 299 < 300
    assert [s.product for s in run(301).plan.segments] == [MONTHLY] * 3  # 301 > 300


# --- 5.4 gas-year boundary --------------------------------------------------------------

def test_period_crossing_1_october_splits_at_the_boundary_with_old_and_new_rows():
    table = make_table(
        make_row(eic=ENTRY.eic, direction="Entry", valid_from="2025-10-01", valid_to="2026-09-30", prices={"D_Sep": 10.0}),
        make_row(eic=EXIT.eic, direction="Exit", valid_from="2025-10-01", valid_to="2026-09-30", prices={"D_Sep": 5.0}),
        make_row(eic=ENTRY.eic, direction="Entry", valid_from="2026-10-01", valid_to=None, prices={"D_Oct": 20.0}),
        make_row(eic=EXIT.eic, direction="Exit", valid_from="2026-10-01", valid_to=None, prices={"D_Oct": 8.0}),
    )
    result = calculate_route(table, ENTRY, EXIT, date(2026, 9, 20), date(2026, 10, 10))
    assert [(s.start, s.end, s.product) for s in result.plan.segments] == [
        (date(2026, 9, 20), date(2026, 9, 30), DAILY),
        (date(2026, 10, 1), date(2026, 10, 10), DAILY),
    ]
    old, new = result.plan.segments
    assert old.price == 11 * (10 + 5)   # September days at the old tariff
    assert new.price == 10 * (20 + 8)   # October days at the new tariff
    assert "entry from 2025-10-01" in old.tariff_used and "(open-ended)" not in old.tariff_used
    assert "entry from 2026-10-01 (open-ended)" in new.tariff_used


def test_open_ended_row_prices_a_far_future_period():
    table = two_point_table(valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, ENTRY, EXIT, date(2029, 5, 1), date(2029, 5, 10))
    assert isinstance(result, RouteResult)
    assert result.plan.segments[0].tariff_used.count("open-ended") == 2


# --- 5.5 validity errors ------------------------------------------------------------

def test_end_before_start_is_a_message():
    table = two_point_table()
    result = calculate_route(table, ENTRY, EXIT, date(2026, 1, 10), date(2026, 1, 9))
    assert isinstance(result, RouteError) and "invalid" in result.message


@pytest.mark.parametrize("start,end", [(None, date(2026, 1, 9)), (date(2026, 1, 9), None), (None, None)])
def test_blank_dates_are_a_message(start, end):
    result = calculate_route(two_point_table(), ENTRY, EXIT, start, end)
    assert isinstance(result, RouteError) and "invalid" in result.message


def test_same_physical_point_is_not_a_route():
    entry = next(p for p in points.entries() if p.name == "Csanádpalota")
    exit_ = next(p for p in points.exits() if p.name == "Csanádpalota")
    table = make_table(
        make_row(eic=entry.eic, direction="Entry"), make_row(eic=exit_.eic, direction="Exit")
    )
    result = calculate_route(table, entry, exit_, date(2026, 1, 1), date(2026, 1, 5))
    assert isinstance(result, RouteError) and "not possible" in result.message


def test_wrong_direction_pair_is_not_a_route():
    result = calculate_route(two_point_table(), EXIT, ENTRY, date(2026, 1, 1), date(2026, 1, 5))
    assert isinstance(result, RouteError) and "not possible" in result.message


def test_period_before_the_earliest_row_names_the_point():
    table = two_point_table(valid_from="2025-10-01")
    result = calculate_route(table, ENTRY, EXIT, date(2025, 9, 25), date(2025, 10, 5))
    assert isinstance(result, RouteError)
    assert "No tariff" in result.message and ENTRY.cleaned_name in result.message and "2025-09-25" in result.message


def test_missing_exit_row_names_the_exit():
    table = make_table(make_row(eic=ENTRY.eic, direction="Entry"))
    result = calculate_route(table, ENTRY, EXIT, date(2026, 1, 1), date(2026, 1, 5))
    assert isinstance(result, RouteError) and EXIT.cleaned_name in result.message


# --- 5.6 totals, per-MWh and FX --------------------------------------------------------

def make_result(total, days_start=date(2026, 12, 5), days_end=date(2027, 1, 15), fx=None):
    plan = Plan(days_start, days_end, (), Fraction(total), Fraction(total))
    return RouteResult(ENTRY, EXIT, plan, fx, None)


def test_forty_two_day_huf_per_mwh():
    result = make_result("2145.47")
    assert result.days == 42
    assert money.format_decimal(result.huf_per_mwh, 4) == "2128.4425"
    assert money.format_decimal(result.huf_per_mwh, 1) == "2128.4"


def test_exact_2128_4_huf_per_mwh_is_5_3210_eur_at_rate_400():
    result = make_result("2145.4272", fx=Fraction(400))  # 2145.4272 / 1008 x 1000 = 2128.4 exactly
    assert result.huf_per_mwh == Fraction("2128.4")
    assert money.format_decimal(result.eur_per_mwh, 4) == "5.3210"


def test_no_rate_means_no_eur_figure():
    result = make_result("2145.47")
    assert result.eur_per_mwh is None and result.all_daily_eur_per_mwh is None


def test_totals_baseline_and_saving_through_the_route():
    table = two_point_table({"M_Dec": 100.0, "D_Dec": 4.0}, {"M_Dec": 100.0, "D_Dec": 4.0}, valid_from="2026-10-01", valid_to=None)
    result = calculate_route(table, ENTRY, EXIT, date(2026, 12, 1), date(2026, 12, 31), "400")
    assert result.huf_per_kwh_h == 200                       # monthly: 100 + 100
    assert result.plan.all_daily_total == 31 * 8             # daily: 31 x (4 + 4)
    assert result.plan.saving == 31 * 8 - 200
    assert result.fx_rate == 400 and result.fx_message is None
    assert result.eur_per_mwh == Fraction(200) / (24 * 31) * 1000 / 400


@pytest.mark.parametrize("text,rate,has_message", [
    ("", None, False), ("   ", None, False), (None, None, False),
    ("400", Fraction(400), False), ("395,5", Fraction("395.5"), False), (" 400.25 ", Fraction("400.25"), False),
    ("0", None, True), ("-3", None, True), ("abc", None, True), ("1/2", None, True), ("nan", None, True),
])
def test_fx_rate_parsing(text, rate, has_message):
    parsed, message = parse_fx_rate(text)
    assert parsed == rate
    assert (message is not None) == has_message


def test_invalid_rate_keeps_the_huf_result_and_carries_a_message():
    table = two_point_table()
    result = calculate_route(table, ENTRY, EXIT, date(2026, 1, 1), date(2026, 1, 3), "abc")
    assert isinstance(result, RouteResult)
    assert result.eur_per_mwh is None and "positive number" in result.fx_message


def test_optimizer_choice_never_depends_on_the_rate():
    table = two_point_table({"M_Dec": 100.0, "D_Dec": 4.0}, {"M_Dec": 100.0, "D_Dec": 4.0}, valid_from="2026-10-01", valid_to=None)
    shapes = {
        rate: [(s.start, s.end, s.product, s.price) for s in calculate_route(table, ENTRY, EXIT, date(2026, 11, 15), date(2027, 1, 15), rate).plan.segments]
        for rate in ("", "1", "400", "99999")
    }
    assert len({tuple(v) for v in shapes.values()}) == 1
