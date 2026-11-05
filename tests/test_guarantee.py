"""Bank Guarantee Calculator rules (Eustream, Operational Order 7.6.2). Expected
figures are worked out by hand from the tariff cells."""

import warnings
from datetime import date
from fractions import Fraction

import pytest

from core import fee, guarantee, points, tariffs
from core.guarantee import AUCTION, BOOKED, CEGHIX_MESSAGE, calculate_guarantee
from core.points import EUSTREAM, EXIT, Point

from .helpers import make_row, make_table

EIC = "21Z000000000358C"
POINT = Point(EUSTREAM, "Test point", "SK>HU", EIC, EXIT)


def eus_row(valid_from, valid_to=None, prices=None):
    return make_row(eic=EIC, direction="Exit", valid_from=valid_from, valid_to=valid_to, operator=EUSTREAM,
                    currency="EUR", unit="kWh/h", prices=prices)


TABLE = make_table(eus_row("2025-10-01"))  # Year 1000, quarters 300, months 100, days 4 EUR per kWh/h


def guarantee_for(table, instrument, capacity, unit, stage, ceghix=None, **selection):
    start, end = fee.resolve_period(instrument, **selection)
    return calculate_guarantee(table, POINT, instrument, start, end, capacity, unit, stage, ceghix)


# --- CEGHIX and the GfON rate ----------------------------------------------------------------

def test_gfon_rate_is_ceghix_plus_one_times_0_85_percent():
    assert guarantee.gfon_rate(Fraction(30)) == Fraction("0.2635")
    assert guarantee.gfon_rate(Fraction(40)) == Fraction("0.3485")
    assert guarantee.gfon_rate(Fraction("30.12")) == Fraction("0.264520")  # not rounded


@pytest.mark.parametrize("text", ["", None, "0", "-5", "abc"])
def test_ceghix_must_be_a_positive_number(text):
    assert guarantee.parse_ceghix(text) == fee.FeeError(CEGHIX_MESSAGE)
    result = guarantee_for(TABLE, fee.MONTH, "10", "kWh/h", BOOKED, text, year=2026, month=2)
    assert result == fee.FeeError(CEGHIX_MESSAGE)


def test_ceghix_accepts_a_decimal_comma():
    assert guarantee.parse_ceghix("30,5") == Fraction("30.5")


def test_auction_ignores_the_ceghix_box():
    result = guarantee_for(TABLE, fee.MONTH, "10", "kWh/h", AUCTION, "abc", year=2026, month=2)
    assert result.gfon_fee is None and result.gfon_fee_guarantee is None


def test_capacity_and_tariff_messages_come_from_tab_2():
    assert guarantee_for(TABLE, fee.MONTH, "0", "kWh/h", BOOKED, "30", year=2026, month=2) == \
        fee.FeeError(fee.CAPACITY_MESSAGE)
    missing = guarantee_for(TABLE, fee.MONTH, "10", "kWh/h", BOOKED, "30", year=2025, month=9)
    assert isinstance(missing, fee.NoTariffError)


# --- Eustream rule on hand-made rows ---------------------------------------------------------

def test_quarter_guarantees_two_of_three_months():
    # 10 kWh/h x 300 = 3,000.00, invoiced 1,000.00 a month. GfON at CEGHIX 99: 0.85 EUR/MWh;
    # 0.24 MWh a day x 92 days = 22.08 MWh -> 18.768; October and December, 62 days = 14.88 MWh -> 12.648.
    result = guarantee_for(TABLE, fee.QUARTER, "10", "kWh/h", BOOKED, "99", year=2026, quarter=4)
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (300000, 200000)
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (1877, 1265)
    assert result.total_guarantee == 201265


def test_gas_year_takes_the_two_dearest_months_across_a_tariff_change():
    # 10 kWh/h at Year 1200 until April 2026 = 1,000.00 a month, at 2400 from May = 2,000.00 a month.
    table = make_table(eus_row("2025-10-01", "2026-04-30", {"Year": 1200.0}), eus_row("2026-05-01", None, {"Year": 2400.0}))
    result = guarantee_for(table, fee.GAS_YEAR, "10", "kWh/h", AUCTION, gas_year=2025)
    assert [line.amount for line in result.fee.invoice] == [100000] * 7 + [200000] * 5
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (1700000, 400000)
    assert result.total_guarantee == 400000


def test_gas_year_gfon_uses_the_two_31_day_months():
    # 0.24 MWh a day: 365 days = 87.6 MWh -> 74.46; two 31-day months = 14.88 MWh -> 12.648.
    result = guarantee_for(TABLE, fee.GAS_YEAR, "10", "kWh/h", BOOKED, "99", gas_year=2025)
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (7446, 1265)


def test_month_in_kwh_d_guarantees_the_whole_fee():
    # 240 kWh/d = 10 kWh/h x 100 = 1,000.00; February 2026: 0.24 MWh x 28 = 6.72 MWh -> 5.712.
    result = guarantee_for(TABLE, fee.MONTH, "240", "kWh/d", BOOKED, "99", year=2026, month=2)
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (100000, 100000)
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (571, 571)
    assert result.total_guarantee == 100571


def test_day_at_auction_has_no_gfon():
    result = guarantee_for(TABLE, fee.DAY, "10", "kWh/h", AUCTION, day=date(2026, 2, 3))
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (4000, 4000)
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (None, None)
    assert result.total_guarantee == 4000


def test_gfon_rounds_half_up_to_cents():
    # 125 kWh/h on one day = 3 MWh x (CEGHIX 29 + 1) x 0.0085 = 0.765 -> 0.77 (half to even would give 0.76).
    result = guarantee_for(TABLE, fee.DAY, "125", "kWh/h", BOOKED, "29", day=date(2026, 2, 3))
    assert result.gfon_fee == 77


def test_only_eustream_has_a_rule():
    assert list(guarantee.GUARANTEE_RULES) == [EUSTREAM]


# --- the spec's worked figures on the real tariff file ----------------------------------------

@pytest.fixture(scope="module")
def real():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        table = tariffs.load_tariffs(tariffs.DEFAULT_PATH).table
    catalog = points.build_catalog(table)
    point = next(p for p in catalog.singles_of(EUSTREAM) if p.name == "Balassagyarmat" and p.flow == "SK>HU")
    return table, point


def real_guarantee(real, instrument, capacity, unit, stage, ceghix=None, **selection):
    table, point = real
    start, end = fee.resolve_period(instrument, **selection)
    return calculate_guarantee(table, point, instrument, start, end, capacity, unit, stage, ceghix)


def test_balassagyarmat_quarter_booked_and_at_auction(real):
    booked = real_guarantee(real, fee.QUARTER, "100000", "kWh/h", BOOKED, "30", year=2026, quarter=4)
    assert (booked.capacity_fee, booked.capacity_fee_guarantee) == (36134400, 24089600)
    assert (booked.gfon_fee, booked.gfon_fee_guarantee) == (5818080, 3920880)
    assert booked.total_guarantee == 28010480
    auction = real_guarantee(real, fee.QUARTER, "100000", "kWh/h", AUCTION, year=2026, quarter=4)
    assert auction.total_guarantee == 24089600


def test_balassagyarmat_gas_year_across_the_may_2026_tariff(real):
    result = real_guarantee(real, fee.GAS_YEAR, "10000", "kWh/h", BOOKED, "40", gas_year=2025)
    assert [line.amount for line in result.fee.invoice] == [730000] * 7 + [803000] * 5
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (9125000, 1606000)
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (3052860, 518568)
    assert result.total_guarantee == 2124568


def test_balassagyarmat_month_in_kwh_d_and_day_at_auction(real):
    month = real_guarantee(real, fee.MONTH, "2400000", "kWh/d", BOOKED, "30", year=2027, month=1)
    assert (month.capacity_fee, month.capacity_fee_guarantee) == (12045600, 12045600)
    assert (month.gfon_fee, month.gfon_fee_guarantee) == (1960440, 1960440)
    assert month.total_guarantee == 14006040
    day = real_guarantee(real, fee.DAY, "100000", "kWh/h", AUCTION, day=date(2026, 12, 5))
    assert (day.capacity_fee, day.capacity_fee_guarantee, day.total_guarantee) == (789600, 789600, 789600)
    assert month.total_guarantee + day.total_guarantee + 28010480 == 42806120  # the spec's list total
