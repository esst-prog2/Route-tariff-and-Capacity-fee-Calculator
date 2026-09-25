from datetime import date

from core import periods


def test_quarters_follow_the_calendar():
    assert periods.quarter_period(2026, 4) == (date(2026, 10, 1), date(2026, 12, 31))
    assert periods.quarter_period(2027, 1) == (date(2027, 1, 1), date(2027, 3, 31))
    assert periods.quarter_period(2027, 2) == (date(2027, 4, 1), date(2027, 6, 30))
    assert periods.quarter_period(2027, 3) == (date(2027, 7, 1), date(2027, 9, 30))


def test_quarter_and_month_columns():
    assert periods.quarter_column(4) == "Q4_Oct"
    assert periods.quarter_column(1) == "Q1_Jan"
    assert periods.month_column(5) == "M_Maj"  # Hungarian abbreviation for May
    assert periods.day_column(5) == "D_Maj"
    assert periods.month_column(10) == "M_Oct"
    assert len(periods.PRICE_COLUMNS) == 1 + 4 + 12 + 12


def test_leap_year_february():
    assert periods.month_last(2028, 2) == date(2028, 2, 29)
    assert periods.month_last(2027, 2) == date(2027, 2, 28)
    assert periods.days_in_period(date(2028, 2, 1), date(2028, 2, 29)) == 29


def test_gas_year_boundaries():
    assert periods.gas_year_start_year(date(2026, 9, 30)) == 2025
    assert periods.gas_year_start_year(date(2026, 10, 1)) == 2026
    assert periods.gas_year_start_year(date(2027, 1, 15)) == 2026
    assert periods.gas_year_period(2025) == (date(2025, 10, 1), date(2026, 9, 30))
    assert periods.gas_year_label(2025) == "2025/26"


def test_period_days_are_inclusive():
    assert periods.days_in_period(date(2026, 12, 5), date(2027, 1, 15)) == 42
    assert periods.days_in_period(date(2026, 12, 5), date(2026, 12, 5)) == 1


def test_month_slices_partial_edges():
    slices = periods.month_slices(date(2026, 12, 5), date(2027, 1, 15))
    assert [(s.year, s.month, s.days, s.full) for s in slices] == [
        (2026, 12, 27, False),
        (2027, 1, 15, False),
    ]


def test_month_slices_period_crossing_1_october():
    slices = periods.month_slices(date(2026, 9, 20), date(2026, 10, 10))
    assert [(s.month, s.first, s.last, s.full) for s in slices] == [
        (9, date(2026, 9, 20), date(2026, 9, 30), False),
        (10, date(2026, 10, 1), date(2026, 10, 10), False),
    ]


def test_month_slices_full_month_between_partials():
    slices = periods.month_slices(date(2026, 11, 15), date(2027, 1, 15))
    assert [(s.month, s.full) for s in slices] == [(11, False), (12, True), (1, False)]


def test_month_slices_span_years_and_full_months():
    slices = periods.month_slices(date(2026, 10, 1), date(2027, 3, 31))
    assert [s.month for s in slices] == [10, 11, 12, 1, 2, 3]
    assert all(s.full for s in slices)
