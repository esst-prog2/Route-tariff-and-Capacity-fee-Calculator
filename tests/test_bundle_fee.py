"""Bundled points on tab 2: two sides priced independently, and the optional
EUR total. Figures are from the real tariff file."""

from datetime import date
from fractions import Fraction

import pytest

from core import fee, money, points, tariffs
from core.fee import QUARTER, BundleFeeResult, EurTotal, NoTariffError, RatesNeeded, resolve_period
from core.tariffs import load_tariffs

from .helpers import make_row, make_table

MOSON = "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)"


@pytest.fixture(scope="module")
def real():
    table = load_tariffs(tariffs.DEFAULT_PATH).table
    return table, points.build_catalog(table)


def bundle(catalog, label):
    return next(b for b in catalog.bundles if b.label() == label)


def q4_2026(real, label, capacity="50,000"):
    table, catalog = real
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    return fee.calculate_bundle_fee(table, bundle(catalog, label), QUARTER, start, end, capacity)


# --- 4.1 two sides ---------------------------------------------------------------------------

def test_bundled_quarter_two_currencies(real):
    result = q4_2026(real, MOSON)
    assert isinstance(result, BundleFeeResult)
    gca, fgsz = result.sides
    assert (gca.point.tso, gca.point.direction, fgsz.point.tso, fgsz.point.direction) == ("GCA", "Exit", "FGSZ", "Entry")
    assert gca.capacity == fgsz.capacity == Fraction(50_000, 24)
    assert (gca.price, fgsz.price) == (Fraction("1.2508"), Fraction("375.627714"))  # GCA: 1.25082191 rounded
    assert (gca.currency, money.format_amount(gca.total, "EUR")) == ("EUR", "2,605.83")  # 50,000 / 24 x 1.2508 = 2,605.833
    assert (fgsz.currency, money.format_amount(fgsz.total, "HUF")) == ("HUF", "782,558")


def test_each_side_uses_its_own_unit(real):
    result = q4_2026(real, "Kireevo/Zaychar BG>RS (Bulgartransgaz + Gastrans)")
    bg, gastrans = result.sides
    assert (bg.unit, bg.capacity) == ("kWh/d", 50_000)
    assert (gastrans.unit, gastrans.capacity) == ("kWh/h", Fraction(50_000, 24))


def two_sided_table():
    eic = "21Z000000000003C"
    return make_table(
        make_row(eic=eic, direction="Exit", operator="GCA", currency="EUR", name="Mosonmagyaróvár - AT (AT>HU)",
                 valid_from="2026-10-01", valid_to=None),
        make_row(eic=eic, direction="Entry", name="Mosonmagyaróvár - HU (AT>HU)",
                 valid_from="2027-01-01", valid_to=None),
    )


def test_one_side_of_a_bundle_has_no_tariff():
    table = two_sided_table()
    moson = points.build_catalog(table).bundles[0]
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = fee.calculate_bundle_fee(table, moson, QUARTER, start, end, "50000")
    assert isinstance(result, NoTariffError)
    assert result.message == ("No tariff exists for the FGSZ entry side (Mosonmagyaróvár (AT>HU)) on 2026-10-01.")


def test_bundle_side_whose_tariff_ends_inside_the_period_names_the_first_day_without_one():
    eic = "21Z000000000003C"
    table = make_table(
        make_row(eic=eic, direction="Exit", operator="GCA", currency="EUR", name="Mosonmagyaróvár - AT (AT>HU)",
                 valid_from="2026-10-01", valid_to=None),
        make_row(eic=eic, direction="Entry", name="Mosonmagyaróvár - HU (AT>HU)",
                 valid_from="2026-10-01", valid_to="2026-11-15"),
    )
    moson = points.build_catalog(table).bundles[0]
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = fee.calculate_bundle_fee(table, moson, QUARTER, start, end, "50000")
    assert isinstance(result, NoTariffError)
    # The entry side has a tariff on 1 October; the first day it has none is 16 November.
    assert result.message == ("No tariff exists for the FGSZ entry side (Mosonmagyaróvár (AT>HU)) on 2026-11-16.")


def test_bundle_capacity_error_comes_before_tariff_check():
    table = two_sided_table()
    moson = points.build_catalog(table).bundles[0]
    start, end = resolve_period(QUARTER, year=2026, quarter=4)
    result = fee.calculate_bundle_fee(table, moson, QUARTER, start, end, "abc")
    assert result.message == fee.CAPACITY_MESSAGE


def test_bundle_year_list_starts_at_the_later_side():
    table = two_sided_table()
    moson = points.build_catalog(table).bundles[0]
    assert fee.gas_year_choices(table, moson, date(2026, 10, 13)) == [2026, 2027, 2028]
    assert fee.gas_year_choices(table, moson.exit, date(2026, 10, 13)) == [2026, 2027, 2028]
    assert fee.calendar_year_choices(table, moson, date(2026, 10, 13))[0] == 2026


# --- 4.2 EUR total -----------------------------------------------------------------------------

def test_eur_total_after_the_rate_is_typed(real):
    total = fee.bundle_eur_total(q4_2026(real, MOSON), {"HUF": "395.5"})
    assert total == EurTotal(458_448, (("HUF", Fraction("395.5")),))
    assert money.format_amount(total.amount, "EUR") == "4,584.48"  # 2,605.83 + 782,558 / 395.5 = 2,605.83 + 1,978.6549


def test_rate_with_decimal_comma(real):
    assert fee.bundle_eur_total(q4_2026(real, MOSON), {"HUF": "395,5"}).amount == 458_448


def test_rate_missing(real):
    needed = fee.bundle_eur_total(q4_2026(real, MOSON), {"HUF": ""})
    assert needed == RatesNeeded(("HUF",), ())
    assert needed.message == "Enter the HUF per EUR rate to see the EUR total."


@pytest.mark.parametrize("text", ["0", "-400", "abc"])
def test_invalid_rate_gives_a_message(real, text):
    needed = fee.bundle_eur_total(q4_2026(real, MOSON), {"HUF": text})
    assert needed == RatesNeeded((), ("HUF",))
    assert needed.message == "The HUF per EUR rate must be a positive number."


def test_two_rates_needed(real):
    result = q4_2026(real, "Csanádpalota RO>HU (Transgaz + FGSZ)")
    assert result.rate_currencies == ["RON", "HUF"]
    assert fee.bundle_eur_total(result, {"HUF": "400"}) == RatesNeeded(("RON",), ())
    assert fee.bundle_eur_total(result, {}).message == "Enter the RON per EUR and HUF per EUR rates to see the EUR total."
    ron, huf = result.sides
    total = fee.bundle_eur_total(result, {"RON": "5", "HUF": "400"})
    expected = Fraction(ron.total, 100) / 5 + Fraction(huf.total) / 400
    assert total.amount == money.round_minor(expected, "EUR")
    assert total.rates == (("RON", Fraction(5)), ("HUF", Fraction(400)))


def test_both_sides_in_eur(real):
    result = q4_2026(real, "Kulata/Sidirokastron BG>GR (Bulgartransgaz + DESFA)")
    assert result.rate_currencies == []
    total = fee.bundle_eur_total(result, {})
    assert total.amount == result.exit.total + result.entry.total and total.rates == ()


# --- 4.3 two invoices ----------------------------------------------------------------------------

def test_two_invoices_for_a_bundle(real):
    gca, fgsz = q4_2026(real, MOSON).sides
    assert [money.format_amount(line.amount, "EUR") for line in gca.invoice] == ["868.61", "868.61", "868.61"]  # 2,605.83 / 3
    assert [money.format_amount(line.amount, "HUF") for line in fgsz.invoice] == ["260,853", "260,853", "260,852"]  # 782,558 / 3 = 260,852.67
    assert sum(line.amount for line in gca.invoice) == gca.total
    assert sum(line.amount for line in fgsz.invoice) == fgsz.total


# --- 7.2 products across tariff changes ---------------------------------------------------------

def gca_gas_year(real):
    table, catalog = real
    gca_exit = bundle(catalog, MOSON).exit
    start, end = resolve_period(fee.GAS_YEAR, gas_year=2026)
    return fee.calculate_fee(table, gca_exit, fee.GAS_YEAR, start, end, "50,000")


def test_gas_year_across_a_calendar_year_tariff_change(real):
    result = gca_gas_year(real)
    assert result.part_prices == (Fraction("3.97"), Fraction("4.1"))
    assert [(p.first, p.last) for p in result.parts] == [
        (date(2026, 10, 1), date(2026, 12, 31)), (date(2027, 1, 1), date(2027, 9, 30)),
    ]
    # Gas Connect Austria bills each month 1/12 of the tariff valid in it, not weighted by days.
    assert result.price == (3 * Fraction("3.97") + 9 * Fraction("4.10")) / 12 == Fraction("4.0675")
    assert money.format_amount(result.total, "EUR") == "8,473.96"  # 50,000 / 24 x 4.0675 = 8,473.958
    assert result.tariff_used == ("from 2026-01-01 for 2026-10-01 to 2026-12-31; "
                                  "from 2027-01-01 (open-ended) for 2027-01-01 to 2027-09-30")


def test_months_follow_the_tariff_valid_in_them(real):
    result = gca_gas_year(real)
    assert [money.format_amount(line.amount, "EUR") for line in result.invoice] == [
        # Each month bills 1/12 of its own tariff: 50,000 / 24 x 3.97 / 12 = 689.236 for Oct-Dec and
        # 50,000 / 24 x 4.10 / 12 = 711.806 for Jan-Sep; the 7 leftover cents of 8,473.96 go to the
        # largest fractions (Oct-Dec), then to the earliest months (Jan-Apr).
        "689.24", "689.24", "689.24", "711.81", "711.81", "711.81",
        "711.81", "711.80", "711.80", "711.80", "711.80", "711.80",
    ]
    assert sum(line.amount for line in result.invoice) == result.total


def test_period_with_one_row_keeps_one_price_and_the_day_split(real):
    result = q4_2026(real, MOSON).exit
    assert len(result.parts) == 1 and result.part_prices == (result.price,)
    assert result.tariff_used == "from 2026-01-01"
