from datetime import date
from fractions import Fraction

import pytest

from core import fee, money, points
from core.fee import (DAY, GAS_YEAR, MONTH, QUARTER, FeeError, FeeResult,
                      calculate_fee, resolve_period)
from core.tariffs import load_tariffs, resolve_tariff_path

from .helpers import make_row, make_table

POINT = next(p for p in points.entries() if p.name == "Kiskundorozsma 2")


def table_with(prices, valid_from="2026-10-01", valid_to=None):
    return make_table(make_row(eic=POINT.eic, direction="Entry", valid_from=valid_from, valid_to=valid_to, prices=prices))


# --- 6.1 period resolution -------------------------------------------------------------

def test_2026_q4_is_october_to_december():
    assert resolve_period(QUARTER, year=2026, quarter=4) == (date(2026, 10, 1), date(2026, 12, 31))


def test_other_period_kinds():
    assert resolve_period(GAS_YEAR, gas_year=2025) == (date(2025, 10, 1), date(2026, 9, 30))
    assert resolve_period(MONTH, year=2028, month=2) == (date(2028, 2, 1), date(2028, 2, 29))
    assert resolve_period(DAY, day=date(2026, 12, 5)) == (date(2026, 12, 5), date(2026, 12, 5))
    assert resolve_period(QUARTER, year=2027, quarter=1) == (date(2027, 1, 1), date(2027, 3, 31))


@pytest.mark.parametrize("kwargs", [
    {"instrument": DAY}, {"instrument": QUARTER, "year": 2026}, {"instrument": GAS_YEAR},
    {"instrument": MONTH, "year": 2026}, {"instrument": "within_day"},
])
def test_incomplete_selection_is_a_message(kwargs):
    assert isinstance(resolve_period(**kwargs), FeeError)


# --- 6.2 price cell and exact conversion ---------------------------------------------------

def test_demo_quarter_on_hand_built_prices():
    table = table_with({"Q4_Oct": 751.255428})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, POINT, QUARTER, start, end, "50000")
    assert isinstance(result, FeeResult)
    assert money.format_decimal(result.capacity_kwh_h, 2) == "2083.33"
    assert result.price_column == "Q4_Oct" and result.price == Fraction("751.255428")
    assert money.format_decimal(result.exact_total, 2) == "1565115.48"
    assert result.total == 1_565_115
    assert result.tariff_used == "from 2026-10-01 (open-ended)"


def test_demo_quarter_on_the_sample_file():
    table = load_tariffs(resolve_tariff_path({})).table
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, POINT, QUARTER, start, end, "50,000")
    assert isinstance(result, FeeResult)
    assert result.total == 1_565_115
    assert [line.amount for line in result.invoice] == [527_376, 510_363, 527_376]


@pytest.mark.parametrize("instrument,selection,column", [
    (GAS_YEAR, {"gas_year": 2026}, "Year"),
    (QUARTER, {"year": 2027, "quarter": 2}, "Q2_Apr"),
    (MONTH, {"year": 2027, "month": 5}, "M_Maj"),
    (DAY, {"day": date(2027, 5, 9)}, "D_Maj"),
    (DAY, {"day": date(2026, 11, 2)}, "D_Nov"),
])
def test_each_instrument_reads_exactly_its_price_cell(instrument, selection, column):
    prices = {c: 1.0 for c in ["Year", "Q1_Jan", "Q2_Apr", "Q3_Jul", "Q4_Oct"]}
    prices.update({column: 7.0})
    table = table_with(prices)
    start, end = resolve_period(instrument, **selection)
    result = calculate_fee(table, POINT, instrument, start, end, "24")  # 24 kWh/d = 1 kWh/h
    assert result.price_column == column
    assert result.total == 7


def test_capacity_conversion_is_exact_not_floating_point():
    table = table_with({"M_Dec": 3.0})
    result = calculate_fee(table, POINT, MONTH, date(2026, 12, 1), date(2026, 12, 31), "10")
    assert result.exact_total == Fraction(10, 24) * 3 == Fraction(5, 4)


# --- 6.3 monthly breakdown --------------------------------------------------------------------

@pytest.mark.parametrize("instrument,selection,lines", [
    (GAS_YEAR, {"gas_year": 2026}, 12),
    (QUARTER, {"year": 2026, "quarter": 4}, 3),
    (MONTH, {"year": 2026, "month": 12}, 1),
    (DAY, {"day": date(2026, 12, 5)}, 1),
])
@pytest.mark.parametrize("capacity", ["50000", "1", "12345.678", "999999"])
def test_breakdown_always_sums_to_the_total(instrument, selection, lines, capacity):
    table = table_with({"Year": 3821.19, "Q4_Oct": 751.255428, "M_Dec": 227.284068, "D_Dec": 17.863966})
    start, end = resolve_period(instrument, **selection)
    result = calculate_fee(table, POINT, instrument, start, end, capacity)
    assert len(result.invoice) == lines
    assert sum(line.amount for line in result.invoice) == result.total
    assert sum(line.days for line in result.invoice) == (end - start).days + 1


def test_single_month_and_day_have_one_line_equal_to_the_total():
    table = table_with({"M_Dec": 227.284068, "D_Dec": 17.863966})
    for instrument, selection in ((MONTH, {"year": 2026, "month": 12}), (DAY, {"day": date(2026, 12, 5)})):
        start, end = resolve_period(instrument, **selection)
        result = calculate_fee(table, POINT, instrument, start, end, "50000")
        assert [line.amount for line in result.invoice] == [result.total]


def test_gas_year_lines_follow_calendar_day_counts():
    table = table_with({"Year": 3653.0})
    start, end = resolve_period(GAS_YEAR, gas_year=2027)  # 2027-10-01 .. 2028-09-30 includes leap February
    result = calculate_fee(table, POINT, GAS_YEAR, start, end, "24")
    days = {(line.year, line.month): line.days for line in result.invoice}
    assert days[(2028, 2)] == 29 and sum(days.values()) == 366
    assert result.total == 3653


# --- 6.4 validation ------------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["0", "-5", "abc", "", "  ", None, "1/2", "nan"])
def test_invalid_capacity_is_a_message(bad):
    table = table_with({"Q4_Oct": 1.0})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, POINT, QUARTER, start, end, bad)
    assert isinstance(result, FeeError) and "positive number" in result.message


def test_gas_year_before_the_data_has_no_tariff():
    table = table_with({"Year": 1.0}, valid_from="2025-10-01")
    start, end = resolve_period(GAS_YEAR, gas_year=2020)
    result = calculate_fee(table, POINT, GAS_YEAR, start, end, "50000")
    assert isinstance(result, FeeError)
    assert "No tariff" in result.message and POINT.cleaned_name in result.message


def test_open_ended_row_prices_a_later_year():
    table = table_with({"Year": 5.0})
    start, end = resolve_period(GAS_YEAR, gas_year=2030)
    result = calculate_fee(table, POINT, GAS_YEAR, start, end, "24")
    assert isinstance(result, FeeResult) and result.total == 5 and "open-ended" in result.tariff_used


def test_capacity_with_thousands_separator_or_decimal_comma():
    table = table_with({"M_Dec": 24.0})
    args = (table, POINT, MONTH, date(2026, 12, 1), date(2026, 12, 31))
    assert calculate_fee(*args, "50,000").capacity_kwh_d == 50000
    assert calculate_fee(*args, "50 000").capacity_kwh_d == 50000
    assert calculate_fee(*args, "1234,5").capacity_kwh_d == Fraction("1234.5")


# --- period picker ranges -----------------------------------------------------------------------------

def test_year_lists_run_from_the_earliest_row_to_two_gas_years_after_today():
    table = table_with({"Year": 1.0}, valid_from="2024-10-01")
    today = date(2026, 9, 25)  # gas year 2025/26
    assert fee.gas_year_choices(table, POINT, today) == [2024, 2025, 2026, 2027]
    assert fee.calendar_year_choices(table, POINT, today) == [2024, 2025, 2026, 2027, 2028]


def test_year_lists_start_at_todays_gas_year_when_the_point_has_no_rows():
    table = make_table(make_row(eic="OTHER"))
    assert fee.gas_year_choices(table, POINT, date(2026, 10, 2)) == [2026, 2027, 2028]
