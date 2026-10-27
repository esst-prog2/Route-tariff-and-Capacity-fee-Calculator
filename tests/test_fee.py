from datetime import date
from fractions import Fraction

import pytest

from core import fee, money
from core.fee import (DAY, GAS_YEAR, MONTH, QUARTER, FeeError, FeeResult,
                      calculate_fee, resolve_period)
from core.points import Point
from core.tariffs import DEFAULT_SAMPLE_PATH, load_tariffs

from .helpers import KNOWN_POINTS, make_row, make_table

POINT = next(p for p in KNOWN_POINTS if p.key == ("FGSZ", "21Z000000000505P", "Entry"))


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


def test_an_impossible_period_raises_instead_of_reading_as_an_incomplete_selection():
    # The pickers only offer real months, so month 13 is a bug and must not turn into "Choose a product period."
    with pytest.raises(ValueError):
        resolve_period(MONTH, year=2026, month=13)


# --- 6.2 price cell and exact conversion ---------------------------------------------------

def test_demo_quarter_on_hand_built_prices():
    table = table_with({"Q4_Oct": 751.255428})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, POINT, QUARTER, start, end, "50000")
    assert isinstance(result, FeeResult)
    assert money.format_decimal(result.capacity, 2) == "2083.33"
    assert result.price_column == "Q4_Oct" and result.price == Fraction("751.255428")
    assert money.format_decimal(result.exact_total, 2) == "1565115.48"
    assert result.total == 1_565_115
    assert result.tariff_used == "from 2026-10-01 (open-ended)"


def test_demo_quarter_on_the_sample_file():
    table = load_tariffs(DEFAULT_SAMPLE_PATH).table
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, POINT, QUARTER, start, end, "50,000")
    assert isinstance(result, FeeResult)
    assert result.total == 1_565_115
    assert [line.amount for line in result.invoice] == [521_705, 521_705, 521_705]  # FGSZ: thirds, not days


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


def test_capacity_typed_in_kwh_h_is_used_unchanged_at_a_kwh_h_point():
    table = table_with({"M_Dec": 3.0})
    result = calculate_fee(table, POINT, MONTH, date(2026, 12, 1), date(2026, 12, 31), "10", "kWh/h")
    assert (result.unit, result.capacity, result.capacity_kwh_d) == ("kWh/h", 10, 240)
    assert result.exact_total == 30  # 10 kWh/h x 3


def test_capacity_typed_in_kwh_h_is_multiplied_by_24_at_a_kwh_d_point():
    table = make_table(make_row(eic=BG_POINT.eic, direction="Exit", operator="BGTRGAZ", currency="EUR", unit="kWh/d",
                                valid_from="2026-10-01", valid_to=None, prices={"Q4_Oct": 0.242217}))
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, BG_POINT, QUARTER, start, end, "1,000", "kWh/h")
    assert (result.unit, result.capacity) == ("kWh/d", 24_000)
    assert money.format_amount(result.total, "EUR") == "5,813.21"  # 24,000 x 0.242217 = 5,813.208


def test_the_same_capacity_in_either_unit_costs_the_same():
    table = table_with({"Q4_Oct": 751.255428})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    per_day = calculate_fee(table, POINT, QUARTER, start, end, "48000", "kWh/d")
    per_hour = calculate_fee(table, POINT, QUARTER, start, end, "2000", "kWh/h")
    assert per_day.exact_total == per_hour.exact_total
    assert per_hour.total == 1_502_511  # 2000 x 751.255428 = 1,502,510.856


def test_an_unknown_capacity_unit_is_a_bug():
    table = table_with({"M_Dec": 3.0})
    with pytest.raises(ValueError):
        calculate_fee(table, POINT, MONTH, date(2026, 12, 1), date(2026, 12, 31), "10", "MWh/d")


GCA_POINT = Point(tso="GCA", name="Mosonmagyaróvár", flow="AT>HU", eic="21Z000000000003C", direction="Exit")


def gca_table(prices, valid_from="2026-10-01", valid_to=None):
    return make_table(make_row(eic=GCA_POINT.eic, direction=GCA_POINT.direction, operator="GCA", currency="EUR",
                               valid_from=valid_from, valid_to=valid_to, prices=prices))


def test_gas_connect_austria_bills_the_tariff_rounded_to_4_decimals():
    table = gca_table({"Q4_Oct": 0.34148})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, GCA_POINT, QUARTER, start, end, "500,000", "kWh/h")
    assert result.price == Fraction("0.3415") and result.tariff_decimals == 4
    assert money.format_amount(result.total, "EUR") == "170,750.00"  # 500,000 x 0.3415 (not 170,740.00)


def test_gas_connect_austria_rounds_each_tariff_of_a_period_that_crosses_a_change():
    table = make_table(
        make_row(eic=GCA_POINT.eic, direction=GCA_POINT.direction, operator="GCA", currency="EUR",
                 valid_from="2026-01-01", valid_to="2026-12-31", prices={"Year": 1.00004}),
        make_row(eic=GCA_POINT.eic, direction=GCA_POINT.direction, operator="GCA", currency="EUR",
                 valid_from="2027-01-01", valid_to=None, prices={"Year": 2.00006}),
    )
    start, end = resolve_period(GAS_YEAR, gas_year=2026)
    result = calculate_fee(table, GCA_POINT, GAS_YEAR, start, end, "365", "kWh/h")
    assert result.part_prices == (Fraction("1.0000"), Fraction("2.0001"))
    # GCA bills 1/12 of each month's tariff: 365 x (3 x 1.0000 + 9 x 2.0001) / 12
    assert result.exact_total == 365 * (3 * 1 + 9 * Fraction("2.0001")) / 12


def test_other_tsos_bill_the_tariff_cell_unrounded():
    table = table_with({"Q4_Oct": 0.34148})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, POINT, QUARTER, start, end, "500,000", "kWh/h")
    assert result.tariff_decimals is None and result.total == 170_740  # 500,000 x 0.34148 HUF


def test_equal_month_tsos_put_leftover_cents_on_the_first_months():
    table = gca_table({"Q4_Oct": 0.1})
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, GCA_POINT, QUARTER, start, end, "1000", "kWh/h")
    assert result.equal_months and result.total == 10_000  # 1,000 x 0.1 = 100.00 EUR
    assert [line.amount for line in result.invoice] == [3_334, 3_333, 3_333]  # not 33.70, 32.60, 33.70 by days


@pytest.mark.parametrize("tso,currency,monthly", [
    ("FGSZ", "HUF", 100), ("EUSTR", "EUR", 10_000), ("GCA", "EUR", 10_000), ("NET4GAS", "CZK", 10_000),
])
def test_the_four_tsos_invoice_a_gas_year_in_twelfths(tso, currency, monthly):
    point = Point(tso=tso, name="Somewhere", flow="AT>HU", eic="21Z000000000003C", direction="Exit")
    table = make_table(make_row(eic=point.eic, direction="Exit", operator=tso, currency=currency,
                                valid_from="2026-10-01", valid_to=None, prices={"Year": 12.0}))
    start, end = resolve_period(GAS_YEAR, gas_year=2026)
    result = calculate_fee(table, point, GAS_YEAR, start, end, "100", "kWh/h")
    assert [line.amount for line in result.invoice] == [monthly] * 12  # 100 x 12 = 1,200 / 12 = 100 (HUF, else cents)


def gastrans_table(prices):
    return make_table(make_row(eic=GASTRANS_POINT.eic, direction="Exit", operator="Gastran", currency="EUR",
                               valid_from="2026-10-01", valid_to=None, prices=prices))


def test_gastrans_invoices_a_quarter_in_thirds():
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(gastrans_table({"Q4_Oct": 0.92}), GASTRANS_POINT, QUARTER, start, end, "100", "kWh/h")
    assert result.equal_months
    assert [line.amount for line in result.invoice] == [3_067, 3_067, 3_066]  # 92.00 / 3 = 30.666...


def test_gastrans_still_invoices_a_gas_year_by_days():
    start, end = resolve_period(GAS_YEAR, gas_year=2026)
    result = calculate_fee(gastrans_table({"Year": 3.65}), GASTRANS_POINT, GAS_YEAR, start, end, "100", "kWh/h")
    assert not result.equal_months
    # 100 x 3.65 = 365.00 EUR, 1.00 EUR per day: Oct 31, Nov 30, Dec 31, Jan 31, Feb 28, Mar 31, Apr 30, ...
    assert [line.amount for line in result.invoice] == [
        3_100, 3_000, 3_100, 3_100, 2_800, 3_100, 3_000, 3_100, 3_000, 3_100, 3_100, 3_000]


def test_a_month_product_of_an_equal_month_tso_is_one_line():
    table = gca_table({"M_Dec": 0.5})
    result = calculate_fee(table, GCA_POINT, MONTH, date(2026, 12, 1), date(2026, 12, 31), "100", "kWh/h")
    assert not result.equal_months and [line.amount for line in result.invoice] == [5_000]


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


# --- Gastrans and Bulgartransgaz: own unit, own currency, cents ---------------------------------------

GASTRANS_POINT = next(p for p in KNOWN_POINTS if p.key == ("Gastran", "21Z000000000505P", "Exit"))
BG_POINT = next(p for p in KNOWN_POINTS if p.key == ("BGTRGAZ", "58Z-000000007-KZ", "Exit"))


def test_gastrans_quarter_in_eur_per_kwh_h():
    table = make_table(make_row(eic=GASTRANS_POINT.eic, direction="Exit", operator="Gastran", currency="EUR",
                                valid_from="2026-10-01", valid_to=None, prices={"Q4_Oct": 6.42}))
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, GASTRANS_POINT, QUARTER, start, end, "50000")
    assert (result.unit, result.currency) == ("kWh/h", "EUR")
    assert money.format_decimal(result.capacity, 2) == "2083.33"
    assert result.total == 1_337_500 and money.format_amount(result.total, "EUR") == "13,375.00"


def test_bulgartransgaz_quarter_without_the_division_by_24():
    table = make_table(make_row(eic=BG_POINT.eic, direction="Exit", operator="BGTRGAZ", currency="EUR", unit="kWh/d",
                                valid_from="2026-10-01", valid_to=None, prices={"Q4_Oct": 0.242217}))
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = calculate_fee(table, BG_POINT, QUARTER, start, end, "50,000")
    assert (result.unit, result.capacity) == ("kWh/d", 50_000)
    assert result.exact_total == Fraction("12110.85")
    assert money.format_amount(result.total, "EUR") == "12,110.85"
    assert [money.format_amount(line.amount, "EUR") for line in result.invoice] == ["4,080.83", "3,949.19", "4,080.83"]
    assert sum(line.amount for line in result.invoice) == result.total


def test_sample_figures_for_the_new_tsos():
    table = load_tariffs(DEFAULT_SAMPLE_PATH).table
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    gastrans = calculate_fee(table, GASTRANS_POINT, QUARTER, start, end, "50000")
    bg = calculate_fee(table, BG_POINT, QUARTER, start, end, "50000")
    assert money.format_amount(gastrans.total, "EUR") == "13,375.00"
    assert bg.price == Fraction("0.2422174")  # the full cell; 0.242217 is its 6-decimal rounding
    assert money.format_amount(bg.total, "EUR") == "12,110.87"


def test_interruptible_point_reports_its_capacity_type():
    point = next(p for p in KNOWN_POINTS if p.key == ("Gastran", "58Z-000000007-KZ", "Exit"))
    table = make_table(make_row(eic=point.eic, direction="Exit", operator="Gastran", currency="EUR", capacity="Interruptible"))
    result = calculate_fee(table, point, DAY, date(2026, 1, 5), date(2026, 1, 5), "24")
    assert result.capacity_type == "Interruptible"


@pytest.mark.parametrize("capacity", ["1", "50000", "12345.678"])
def test_eur_invoice_always_sums_to_the_total_in_cents(capacity):
    table = make_table(make_row(eic=BG_POINT.eic, direction="Exit", operator="BGTRGAZ", currency="EUR", unit="kWh/d",
                                valid_from="2026-10-01", valid_to=None, prices={"Year": 0.981251}))
    start, end = resolve_period(GAS_YEAR, gas_year=2026)
    result = calculate_fee(table, BG_POINT, GAS_YEAR, start, end, capacity)
    assert len(result.invoice) == 12 and sum(line.amount for line in result.invoice) == result.total
