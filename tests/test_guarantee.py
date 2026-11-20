"""Bank Guarantee Calculator rules (Eustream, Operational Order 7.6.2). Expected
figures are worked out by hand from the tariff cells."""

import warnings
from datetime import date
from fractions import Fraction

import pytest

from core import fee, guarantee, points, tariffs
from core.guarantee import AUCTION, BOOKED, CEGHIX_MESSAGE, calculate_guarantee
from core.points import ENTRY, EUSTREAM, EXIT, FGSZ, GCA, Point

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


def test_eustream_gca_and_fgsz_have_a_rule_and_only_eustream_is_staged():
    assert list(guarantee.GUARANTEE_RULES) == [EUSTREAM, GCA, FGSZ]
    assert list(guarantee.GUARANTEE_NOTES) == [EUSTREAM, GCA, FGSZ]
    assert guarantee.STAGED_TSOS == {EUSTREAM}


def test_eustream_still_needs_a_stage():
    start, end = fee.resolve_period(fee.MONTH, year=2026, month=2)
    with pytest.raises(ValueError):
        calculate_guarantee(TABLE, POINT, fee.MONTH, start, end, "10", "kWh/h", None)


# --- Gas Connect Austria rule on hand-made rows (GTC IV para. 15) -----------------------------

GCA_EIC = "21Z000000000003C"
GCA_POINT = Point(GCA, "Test point", "AT>HU", GCA_EIC, EXIT)


def gca_row(valid_from, valid_to=None, prices=None):
    return make_row(eic=GCA_EIC, direction="Exit", valid_from=valid_from, valid_to=valid_to, operator=GCA,
                    currency="EUR", unit="kWh/h", prices=prices)


GCA_TABLE = make_table(gca_row("2025-10-01"))  # Year 1000, quarters 300, months 100, days 4 EUR per kWh/h


def gca_for(table, instrument, capacity, unit, surcharge=None, stage=None, ceghix=None, **selection):
    start, end = fee.resolve_period(instrument, **selection)
    return calculate_guarantee(table, GCA_POINT, instrument, start, end, capacity, unit, stage, ceghix, surcharge)


def test_gca_quarter_takes_the_first_two_months():
    # 10 kWh/h x 300 = 3,000.00, invoiced 1,000.00 a month; no GfON. Commodity at the exit rate 0.11963:
    # 0.24 MWh a day x 92 days = 22.08 MWh -> 2.64; October and November, 61 days = 14.64 MWh -> 1.75.
    result = gca_for(GCA_TABLE, fee.QUARTER, "10", "kWh/h", year=2026, quarter=4)
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (300000, 200000)
    assert (result.commodity_fee, result.commodity_fee_guarantee) == (264, 175)
    assert result.total_guarantee == 200175
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (None, None)


def test_gca_commodity_rate_by_date_and_direction():
    rate = guarantee.gca_commodity_rate
    assert rate(date(2025, 12, 31), EXIT) == 0  # no rate known before 2026
    assert (rate(date(2026, 1, 1), ENTRY), rate(date(2026, 12, 31), EXIT)) == (Fraction("0.03322"), Fraction("0.11963"))
    assert (rate(date(2027, 1, 1), ENTRY), rate(date(2030, 6, 1), EXIT)) == (Fraction("0.07914"), Fraction("0.2586"))


def test_gca_commodity_rounds_half_up_once():
    # 625 kWh/h x 24 / 1000 = 15 MWh a day; a February 2026 month = 420 MWh x 0.03322 = 13.9524 -> 13.95 at entry.
    entry = Point(GCA, "Test point", "HU>AT", GCA_EIC, ENTRY)
    table = make_table(make_row(eic=GCA_EIC, direction="Entry", operator=GCA, currency="EUR", unit="kWh/h"))
    start, end = fee.resolve_period(fee.MONTH, year=2026, month=2)
    result = calculate_guarantee(table, entry, fee.MONTH, start, end, "625", "kWh/h", None)
    assert (result.commodity_fee, result.commodity_fee_guarantee) == (1395, 1395)


def test_gca_gas_year_takes_the_first_three_months_not_the_dearest():
    # 10 kWh/h at Year 1200 in 2025 = 1,000.00 a month, at 2400 from 1 January 2026 = 2,000.00 a month.
    table = make_table(gca_row("2025-10-01", "2025-12-31", {"Year": 1200.0}), gca_row("2026-01-01", None, {"Year": 2400.0}))
    result = gca_for(table, fee.GAS_YEAR, "10", "kWh/h", gas_year=2025)
    assert [line.amount for line in result.fee.invoice] == [100000] * 3 + [200000] * 9
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (2100000, 300000)


def test_gca_month_in_kwh_d_guarantees_the_whole_fee():
    # 240 kWh/d x 28 days = 6.72 MWh x 0.11963 = 0.80 commodity.
    result = gca_for(GCA_TABLE, fee.MONTH, "240", "kWh/d", year=2026, month=2)
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (100000, 100000)
    assert (result.commodity_fee, result.commodity_fee_guarantee, result.total_guarantee) == (80, 80, 100080)


def test_gca_day_has_no_security_deposit():
    result = gca_for(GCA_TABLE, fee.DAY, "10", "kWh/h", day=date(2026, 2, 3))
    assert (result.capacity_fee, result.commodity_fee) == (4000, 3)  # 0.24 MWh x 0.11963 = 0.03
    assert (result.capacity_fee_guarantee, result.commodity_fee_guarantee, result.total_guarantee) == (None, None, None)
    assert guarantee.is_gca_day(GCA_POINT, fee.DAY) and not guarantee.is_gca_day(POINT, fee.DAY)
    assert not guarantee.is_gca_day(GCA_POINT, fee.MONTH)


def test_gca_ignores_the_stage_and_the_ceghix():
    result = gca_for(GCA_TABLE, fee.MONTH, "10", "kWh/h", stage=BOOKED, ceghix="abc", year=2026, month=2)
    assert (result.capacity_fee_guarantee, result.gfon_fee) == (100000, None)


def test_gca_surcharge_raises_the_first_months():
    # 3,000.00 + 15% = 3,450.00, invoiced 1,150.00 a month; the first two months 2,300.00.
    result = gca_for(GCA_TABLE, fee.QUARTER, "10", "kWh/h", "15", year=2026, quarter=4)
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (345000, 230000)
    assert gca_for(GCA_TABLE, fee.QUARTER, "10", "kWh/h", "-1", year=2026, quarter=4) == \
        fee.FeeError(guarantee.SURCHARGE_MESSAGE)


def test_gca_note_covers_the_rule():
    note = guarantee.GUARANTEE_NOTES[GCA]
    for text in ("first two months", "first three months", "EUR 100,000", "5 working days after", "German one is binding",
                 "commodity charge", "0.03322", "0.11963", "0.07914", "0.2586", "before 1 January 2026"):
        assert text in note


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


def test_mosonmagyarovar_gca_figures_of_the_spec(real):
    table, _ = real
    point = next(p for p in points.build_catalog(table).singles_of(GCA) if p.name == "Mosonmagyaróvár" and p.flow == "AT>HU")

    def gca(instrument, capacity, unit, surcharge=None, **selection):
        start, end = fee.resolve_period(instrument, **selection)
        return calculate_guarantee(table, point, instrument, start, end, capacity, unit, None, None, surcharge)

    def amounts(r):
        return r.capacity_fee, r.capacity_fee_guarantee, r.commodity_fee, r.commodity_fee_guarantee, r.total_guarantee

    quarter = gca(fee.QUARTER, "120000", "kWh/h", year=2026, quarter=4)
    assert [line.amount for line in quarter.fee.invoice] == [5003200] * 3
    assert amounts(quarter) == (15009600, 10006400, 3169716, 2101660, 12108060)
    year = gca(fee.GAS_YEAR, "120000", "kWh/h", gas_year=2025)
    assert [line.amount for line in year.fee.invoice] == [2140000] * 3 + [3970000] * 9
    assert amounts(year) == (42150000, 6420000, 9405789, 0, 6420000)  # no commodity rate in 2025
    year = gca(fee.GAS_YEAR, "120000", "kWh/h", gas_year=2026)
    assert amounts(year)[1:] == (11910000, 23501883, 3169716, 15079716)
    month = gca(fee.MONTH, "2880000", "kWh/d", year=2027, month=1)
    assert amounts(month) == (6267600, 6267600, 2308781, 2308781, 8576381)
    december = gca(fee.MONTH, "150000", "kWh/h", year=2026, month=12)  # the user's example
    assert (december.commodity_fee, december.commodity_fee_guarantee) == (1335071, 1335071)
    day = gca(fee.DAY, "120000", "kWh/h", day=date(2026, 12, 5))
    assert amounts(day) == (261600, None, 34453, None, None)
    surcharged = gca(fee.QUARTER, "120000", "kWh/h", "10", year=2026, quarter=4)
    assert [line.amount for line in surcharged.fee.invoice] == [5503520] * 3
    assert amounts(surcharged) == (16510560, 11007040, 3169716, 2101660, 13108700)
    day_surcharged = gca(fee.DAY, "120000", "kWh/h", "2,5", day=date(2026, 12, 5))
    assert amounts(day_surcharged) == (268140, None, 34453, None, None)

    entry = next(p for p in points.build_catalog(table).singles_of(GCA) if p.name == "VIP Oberkappel" and p.flow == "DE>AT")
    start, end = fee.resolve_period(fee.QUARTER, year=2027, quarter=1)
    oberkappel = calculate_guarantee(table, entry, fee.QUARTER, start, end, "120000", "kWh/h", None)
    assert (oberkappel.commodity_fee, oberkappel.commodity_fee_guarantee) == (2051309, 1344747)


# --- FGSZ rule on hand-made rows (GTC 4.d 7.5) -------------------------------------------------

FGSZ_EIC = "21Z000000000236Q"
FGSZ_EXIT = Point(FGSZ, "Test point", "HU>RO", FGSZ_EIC, EXIT)
FGSZ_ENTRY = Point(FGSZ, "Test point", "RO>HU", FGSZ_EIC, ENTRY)
FGSZ_TABLE = make_table(  # Year 1000, quarters 300, months 100, days 4 HUF per kWh/h, both directions
    make_row(eic=FGSZ_EIC, direction="Exit", operator=FGSZ, valid_to=None),
    make_row(eic=FGSZ_EIC, direction="Entry", operator=FGSZ, valid_to=None),
)


def fgsz_for(point, instrument, capacity, unit="kWh/h", surcharge=None, **selection):
    start, end = fee.resolve_period(instrument, **selection)
    return calculate_guarantee(FGSZ_TABLE, point, instrument, start, end, capacity, unit, None, None, surcharge)


def fgsz_amounts(r):
    return r.capacity_fee, r.commodity_fee, r.capacity_fee_guarantee, r.commodity_fee_guarantee, r.vat, r.total_guarantee


def test_fgsz_quarter_at_an_exit_point():
    # K = 10 kWh/h x 300 = 3,000 HUF -> 1/3 = 1,000. F = 0.24 MWh x 92 days = 22.08 MWh x 29.22 = 645.1776 -> 645;
    # 2/3 x 645.1776 x 0.8005 = 344.31 -> 344. VAT 27% of 1,344 = 362.88 -> 363. Total 1,707.
    result = fgsz_for(FGSZ_EXIT, fee.QUARTER, "10", year=2026, quarter=4)
    assert result.currency == "HUF"
    assert fgsz_amounts(result) == (3000, 645, 1000, 344, 363, 1707)
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (None, None)


def test_fgsz_gas_year_takes_exact_twelfths():
    # K = 10,000 -> 1/12 = 833.33 -> 833. F = 87.6 MWh x 29.22 = 2,559.672; 2/12 x F x 0.8005 = 341.50 -> 342.
    # VAT 27% of 1,175 = 317.25 -> 317. Total 1,492.
    result = fgsz_for(FGSZ_EXIT, fee.GAS_YEAR, "10", gas_year=2026)
    assert fgsz_amounts(result) == (10000, 2560, 833, 342, 317, 1492)


def test_fgsz_month_and_day_take_the_whole_fee():
    # Month: 240 kWh/d = 10 kWh/h x 100 = 1,000; F = 0.24 x 28 = 6.72 MWh x 29.22 = 196.36; x 0.8005 = 157.18 -> 157.
    month = fgsz_for(FGSZ_EXIT, fee.MONTH, "240", "kWh/d", year=2027, month=2)
    assert fgsz_amounts(month) == (1000, 196, 1000, 157, 312, 1469)
    # Day: 10 kWh/h x 4 = 40; F = 0.24 x 29.22 = 7.01; x 0.8005 = 5.61 -> 6; VAT 27% of 46 = 12.42 -> 12.
    day = fgsz_for(FGSZ_EXIT, fee.DAY, "10", day=date(2026, 12, 5))
    assert fgsz_amounts(day) == (40, 7, 40, 6, 12, 58)


def test_fgsz_entry_point_has_no_volume_fee():
    result = fgsz_for(FGSZ_ENTRY, fee.QUARTER, "10", year=2026, quarter=4)
    assert fgsz_amounts(result) == (3000, 0, 1000, 0, 270, 1270)


def test_fgsz_surcharge_raises_the_capacity_part_not_the_volume_fee():
    # 3,000 + 10% = 3,300 -> 1/3 = 1,100; the volume part stays 344; VAT 27% of 1,444 = 389.88 -> 390.
    result = fgsz_for(FGSZ_EXIT, fee.QUARTER, "10", surcharge="10", year=2026, quarter=4)
    assert fgsz_amounts(result) == (3300, 645, 1100, 344, 390, 1834)


def test_fgsz_rounds_each_part_half_away_from_zero():
    # 3 kWh/h quarter: K = 900 -> 300; F = 6.624 MWh x 29.22 = 193.553; 2/3 x F x 0.8005 = 103.29 -> 103;
    # VAT 27% of 403 = 108.81 -> 109. A day at 25 kWh/h: K = 100; F = 0.6 MWh x 29.22 = 17.532 -> 18;
    # x 0.8005 = 14.03 -> 14; VAT 27% of 114 = 30.78 -> 31; total 145.
    assert fgsz_amounts(fgsz_for(FGSZ_EXIT, fee.QUARTER, "3", year=2026, quarter=4)) == (900, 194, 300, 103, 109, 512)
    assert fgsz_amounts(fgsz_for(FGSZ_EXIT, fee.DAY, "25", day=date(2026, 12, 5))) == (100, 18, 100, 14, 31, 145)


def test_fgsz_note_covers_the_rule():
    note = guarantee.GUARANTEE_NOTES[FGSZ]
    for text in ("1/12", "1/3", "29.22 HUF/MWh", "80.05%", "27%", "HUF 10,000,000", "HUF 35,000,000",
                 "60 days after the service period", "0.0833", "5/12", "BB", "7.3"):
        assert text in note


def test_fgsz_figures_of_the_spec(real):
    table, _ = real
    catalog = points.build_catalog(table)

    def fgsz(name, flow, instrument, capacity, unit="kWh/h", surcharge=None, **selection):
        point = next(p for p in catalog.singles_of(FGSZ) if p.name == name and p.flow == flow)
        start, end = fee.resolve_period(instrument, **selection)
        return fgsz_amounts(calculate_guarantee(table, point, instrument, start, end, capacity, unit, None, None,
                                                surcharge))

    assert len(catalog.singles_of(FGSZ)) == 14
    assert fgsz("Csanádpalota", "HU>RO", fee.QUARTER, "100000", year=2026, quarter=4) == \
        (43362631, 6451776, 14454210, 3443098, 4832273, 22729581)
    assert fgsz("Csanádpalota", "HU>RO", fee.GAS_YEAR, "100000", gas_year=2026) == \
        (132648000, 25596720, 11054000, 3415029, 3906638, 18375667)
    assert fgsz("Csanádpalota", "HU>RO", fee.GAS_YEAR, "100000", gas_year=2025) == \
        (132727000, 25596720, 11060583, 3415029, 3908415, 18384027)
    assert fgsz("Csanádpalota", "HU>RO", fee.MONTH, "2400000", "kWh/d", year=2027, month=1) == \
        (19074782, 2173968, 19074782, 1740261, 5620062, 26435105)
    assert fgsz("Csanádpalota", "HU>RO", fee.DAY, "100000", day=date(2026, 12, 5)) == \
        (1047919, 70128, 1047919, 56137, 298095, 1402151)
    assert fgsz("Mosonmagyaróvár", "AT>HU", fee.QUARTER, "100000", year=2026, quarter=4) == \
        (37562771, 0, 12520924, 0, 3380649, 15901573)
    assert fgsz("Csanádpalota", "HU>RO", fee.QUARTER, "100000", surcharge="10", year=2026, quarter=4) == \
        (47698894, 6451776, 15899631, 3443098, 5222537, 24565266)


# --- Auction surcharge -----------------------------------------------------------------------

def guarantee_with_surcharge(table, instrument, capacity, unit, stage, ceghix, surcharge, **selection):
    start, end = fee.resolve_period(instrument, **selection)
    return calculate_guarantee(table, POINT, instrument, start, end, capacity, unit, stage, ceghix, surcharge)


@pytest.mark.parametrize("text", [None, "", "  ", "0"])
def test_blank_or_zero_surcharge_changes_nothing(text):
    plain = guarantee_for(TABLE, fee.QUARTER, "10", "kWh/h", BOOKED, "99", year=2026, quarter=4)
    result = guarantee_with_surcharge(TABLE, fee.QUARTER, "10", "kWh/h", BOOKED, "99", text, year=2026, quarter=4)
    assert result.surcharge == 0
    assert (result.capacity_fee, result.capacity_fee_guarantee, result.gfon_fee, result.gfon_fee_guarantee) == \
        (plain.capacity_fee, plain.capacity_fee_guarantee, plain.gfon_fee, plain.gfon_fee_guarantee)


def test_quarter_surcharge_raises_the_capacity_fee_and_its_guarantee_not_the_gfon():
    # 10 kWh/h x 300 = 3,000.00 + 15% = 3,450.00, invoiced 1,150.00 a month; two months 2,300.00.
    result = guarantee_with_surcharge(TABLE, fee.QUARTER, "10", "kWh/h", BOOKED, "99", "15", year=2026, quarter=4)
    assert result.surcharge == 15
    assert (result.capacity_fee, result.capacity_fee_guarantee) == (345000, 230000)
    assert [line.amount for line in result.fee.invoice] == [115000] * 3
    assert (result.gfon_fee, result.gfon_fee_guarantee) == (1877, 1265)
    assert result.total_guarantee == 231265


def test_surcharge_at_auction_and_for_a_month():
    # 10 kWh/h x 100 = 1,000.00 + 12.5% = 1,125.00; a month guarantees the whole fee.
    result = guarantee_with_surcharge(TABLE, fee.MONTH, "10", "kWh/h", AUCTION, None, "12,5", year=2026, month=2)
    assert (result.capacity_fee, result.capacity_fee_guarantee, result.total_guarantee) == (112500, 112500, 112500)


def test_surcharge_invoice_adds_up_after_rounding():
    # 1 kWh/h x 300 = 300.00 + 0.01% = 300.03, split 100.01 + 100.01 + 100.01.
    result = guarantee_with_surcharge(TABLE, fee.QUARTER, "1", "kWh/h", AUCTION, None, "0.01", year=2026, quarter=4)
    assert result.capacity_fee == 30003
    assert sum(line.amount for line in result.fee.invoice) == 30003
    assert result.capacity_fee_guarantee == 20002


@pytest.mark.parametrize("text", ["-1", "abc"])
def test_surcharge_must_be_zero_or_more(text):
    result = guarantee_with_surcharge(TABLE, fee.MONTH, "10", "kWh/h", BOOKED, "30", text, year=2026, month=2)
    assert result == fee.FeeError(guarantee.SURCHARGE_MESSAGE)
