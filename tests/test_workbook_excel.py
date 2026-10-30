"""The Capacity Fee Workbook recalculated in real Excel, compared figure by figure
with the app's `core.fee` for the same inputs (spec excel-fee-workbook, "Checked
against the app").

Runs only with `pytest -m excel` and only where Excel is installed (Windows,
driven through PowerShell COM by `excel_check.ps1`); every workbook's cases run
in one Excel session."""

from __future__ import annotations

import functools
import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from core import fee, money, periods, points, tariffs
from core.points import Bundle, Point
from core.tariffs import INTERRUPTIBLE
from core.workbook import build_workbook

from .helpers import make_row, make_table

SCRIPT = Path(__file__).with_name("excel_check.ps1")
EXCEL_EPOCH = date(1899, 12, 30)
RATE_CURRENCIES = ("CZK", "HUF", "PLN", "RON")


@functools.cache
def excel_installed() -> bool:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "if ([type]::GetTypeFromProgID('Excel.Application')) { 'yes' }"],
            capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.stdout.strip() == "yes"


pytestmark = [pytest.mark.excel, pytest.mark.skipif("not excel_installed()", reason="Excel is not installed")]

OUTPUTS = ["msg_main", "out_heading", "out_eur_total", "out_eur_caption", "out_eur_msg"] + [
    f"out{n}_{field}" for n in (1, 2) for field in (
        "heading", "tso", "direction", "capacity", "price", "total", "tariff_used", "caption", "rounding",
        "interruptible", "equal", "months", "days", "amounts", "invoice_total")]
LIST_FIELDS = ("months", "days", "amounts")


# --- cases and the app's figures for them ---------------------------------------------------------

@dataclass(frozen=True)
class Case:
    booked: Point | Bundle
    instrument: str
    start: date
    end: date
    capacity: object = 50000  # as typed: a number, or text for an invalid capacity
    unit: str = "kWh/d"
    rates: dict = field(default_factory=dict)  # currency -> units per 1 EUR (missing = blank box)

    def describe(self, catalog) -> str:
        return f"{point_label(self.booked, catalog)} | {self.instrument} {fee.dates_text(self.start, self.end)} | " \
               f"{self.capacity} {self.unit} | {self.rates}"


def point_label(booked, catalog) -> str:
    if isinstance(booked, Bundle):
        return booked.label()
    return booked.lng_label() if booked.is_lng else booked.fee_label(catalog.capacity_type(booked))


def serial(day: date) -> int:
    return (day - EXCEL_EPOCH).days


def inputs(case: Case, catalog) -> dict:
    """The workbook's named inputs for a case, in the order a user would fill them."""
    booked = case.booked
    if isinstance(booked, Bundle):
        values = {"in_booking": "Bundled"}
    elif booked.is_lng:
        values = {"in_booking": "LNG entry"}
    else:
        values = {"in_booking": "Single side", "in_tso": booked.tso_name}
    values["in_point"] = point_label(booked, catalog)
    values["in_instrument"] = fee.INSTRUMENT_LABELS[case.instrument]
    start = case.start
    period = {
        fee.GAS_YEAR: lambda: periods.gas_year_label(start.year),
        fee.QUARTER: lambda: f"{start.year} Q{periods.quarter_of_month(start.month)}",
        fee.MONTH: lambda: f"{start.year}-{start.month:02d}",
        fee.DAY: lambda: None,
    }[case.instrument]()
    values["in_period"] = period
    values["in_day"] = serial(start) if case.instrument == fee.DAY else None
    values["in_capacity"] = case.capacity
    values["in_unit"] = case.unit
    for currency in RATE_CURRENCIES:
        values[f"in_rate_{currency}"] = case.rates.get(currency)
    return values


def fixed(value, places: int) -> str:
    """A number as the app shows it: rounded half up to `places` decimals, no separators."""
    return str(Decimal(str(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def amount(minor: int, currency: str) -> str:
    places = money.CURRENCY_DECIMALS[currency]
    return money.format_decimal(Fraction(minor, 10 ** places), places)


def plain_rate(rate: Fraction) -> str:
    text = money.format_decimal(rate, 4)
    return text.rstrip("0").rstrip(".") if "." in text else text


def expected(table, catalog, case: Case) -> dict:
    """Every output as the app shows it ("" where the app shows nothing)."""
    out = {name: "" for name in OUTPUTS}
    for n in (1, 2):
        for name in LIST_FIELDS:
            out[f"out{n}_{name}"] = [""] * 12
    booked, text = case.booked, str(case.capacity)
    if isinstance(booked, Bundle):
        result = fee.calculate_bundle_fee(table, booked, case.instrument, case.start, case.end, text, case.unit)
    else:
        result = fee.calculate_fee(table, booked, case.instrument, case.start, case.end, text, case.unit)
    if isinstance(result, fee.FeeError):
        out["msg_main"] = result.message
        return out

    label = booked.label() if isinstance(booked, Bundle) else (
        booked.lng_label() if booked.is_lng else f"{booked.tso_name} {booked.fee_label()}")
    out["out_heading"] = (f"{label}: {fee.INSTRUMENT_LABELS[case.instrument].lower()} "
                          f"{fee.dates_text(case.start, case.end)}")
    sides = result.sides if isinstance(booked, Bundle) else (result,)
    for n, r in enumerate(sides, 1):
        p, currency = r.point, r.currency
        put = lambda name, value: out.__setitem__(f"out{n}_{name}", value)
        put("heading", f"{p.tso_name} {p.direction.lower()} {p.cleaned_name}" if isinstance(booked, Bundle) else "")
        put("tso", p.tso_name)
        put("direction", p.direction)
        put("capacity", money.format_decimal(r.capacity, 2))
        put("price", " / ".join(money.format_decimal(v, 4) for v in dict.fromkeys(r.part_prices)))
        put("total", amount(r.total, currency))
        put("invoice_total", amount(r.total, currency))
        put("tariff_used", r.tariff_used)
        rounding = "whole forints" if money.CURRENCY_DECIMALS[currency] == 0 else "cents"
        put("caption", f"All amounts are in {currency}; the total is rounded to {rounding}.")
        put("rounding", "" if r.tariff_decimals is None else
            f"{p.tso_name} bills its tariff rounded to {r.tariff_decimals} decimals.")
        put("interruptible", "This point has no Firm tariff, so Interruptible capacity is priced; "
                             "the TSO can interrupt it." if r.capacity_type == INTERRUPTIBLE else "")
        share = "1/12 of the gas year" if case.instrument == fee.GAS_YEAR else "1/3 of the quarter"
        put("equal", f"{p.tso_name} invoices each month as {share} at the tariff valid in it, whatever the month's "
                     "number of days." if r.equal_months else "")
        pad = [""] * (12 - len(r.invoice))
        put("months", [f"{line.year}-{line.month:02d}" for line in r.invoice] + pad)
        put("days", [str(line.days) for line in r.invoice] + pad)
        put("amounts", [amount(line.amount, currency) for line in r.invoice] + pad)

    if isinstance(booked, Bundle):
        total = fee.bundle_eur_total(result, {c: str(v) for c, v in case.rates.items()})
        if isinstance(total, fee.RatesNeeded):
            out["out_eur_msg"] = total.message
        else:
            out["out_eur_total"] = amount(total.amount, "EUR")
            rates = "; ".join(f"at 1 EUR = {plain_rate(rate)} {currency}" for currency, rate in total.rates)
            out["out_eur_caption"] = "Sum of both sides' totals" + (f", converted {rates}." if rates else
                                                                     ", both in EUR.")
    return out


# --- what the workbook shows, made comparable -------------------------------------------------------

def shown(name: str, value, out: dict, decimal: str):
    """A workbook value as text the way `expected` writes it."""
    if isinstance(value, list):
        return [shown(name, v, out, decimal) for v in value]
    if value == "" or value is None:
        return ""
    if isinstance(value, str):
        return re.sub(rf"(\d){re.escape(decimal)}(\d)", r"\1.\2", value) if decimal != "." else value
    if isinstance(value, (int, float)) and value < -2146820000:
        return f"#ERROR {value}"
    if name.endswith("capacity"):
        return fixed(value, 2)
    if name.endswith("days"):
        return str(int(value))
    places = 2
    if name.startswith(("out1", "out2")) and name[3] in "12":
        currency = out.get(f"{name[:4]}_currency")
        places = money.CURRENCY_DECIMALS.get(currency, 2)
    return fixed(value, places)


def differences(actual: dict, want: dict, decimal: str) -> list[str]:
    found = []
    for name in OUTPUTS:
        got = shown(name, actual.get(name), want, decimal)
        if got != want[name]:
            found.append(f"{name}: workbook {got!r}, app {want[name]!r}")
    return found


def run_excel(workbook: Path, cases: list[dict], tmp: Path) -> tuple[str, list[dict]]:
    cases_path, results_path = tmp / "cases.json", tmp / "results.json"
    cases_path.write_text(json.dumps({"workbook": str(workbook), "cases": cases}), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                    str(SCRIPT), str(cases_path), str(results_path)],
                   check=True, timeout=3600, stdin=subprocess.DEVNULL)
    data = json.loads(results_path.read_text(encoding="utf-8-sig"))
    return data["decimal"], data["results"]


class Checked:
    """One workbook: its cases run in Excel at once, then compared with the app."""

    def __init__(self, table, source: str, tmp: Path, cases: list[Case], extra: list[tuple[dict, list[str]]] = ()):
        self.table = table
        self.catalog = points.build_catalog(table)
        path = tmp / "workbook.xlsx"
        build_workbook(table, self.catalog, source, date.today()).save(path)
        self.cases = cases
        plain = [{"inputs": inputs(c, self.catalog), "read": OUTPUTS} for c in cases]
        raw = [{"inputs": i, "read": r} for i, r in extra]
        self.decimal, results = run_excel(path, plain + raw, tmp)
        self.results, self.extra = results[:len(cases)], results[len(cases):]

    def want(self, i: int) -> dict:
        want = expected(self.table, self.catalog, self.cases[i])
        sides = self.cases[i].booked.sides if isinstance(self.cases[i].booked, Bundle) else (self.cases[i].booked,)
        for n, side in enumerate(sides, 1):  # the currency decides how many decimals a figure has
            want[f"out{n}_currency"] = self.table.rows(*side.key)[0].currency
        return want

    def got(self, i: int) -> dict:
        return {name: shown(name, value, self.want(i), self.decimal) for name, value in self.results[i].items()}

    def all_differences(self) -> list[str]:
        found = []
        for i, case in enumerate(self.cases):
            for difference in differences(self.results[i], self.want(i), self.decimal):
                found.append(f"{case.describe(self.catalog)}: {difference}")
        return found


# --- the real tariff file: every point -------------------------------------------------------------

def find(catalog, label: str):
    for booked in (*catalog.bundles, *catalog.singles, *catalog.lng):
        if point_label(booked, catalog) == label:
            return booked
    raise LookupError(label)


def single(catalog, tso: str, label_start: str) -> Point:
    return next(p for p in catalog.singles_of(tso) if p.fee_label(catalog.capacity_type(p)).startswith(label_start))


def sweep_cases(table, catalog, today: date) -> list[Case]:
    """Every point (bundles as bundles), each with a gas year, a quarter, a month and a day,
    in both units; the periods rotate through each point's year lists, so some have no tariff."""
    rate_sets = [{}, {"HUF": 395.5, "RON": 4.97, "CZK": 24.3, "PLN": 4.25}, {"HUF": 401.25, "RON": "x"}]
    cases = []
    for i, booked in enumerate((*catalog.bundles, *catalog.singles, *catalog.lng)):
        gas_years = fee.gas_year_choices(table, booked, today)
        years = fee.calendar_year_choices(table, booked, today)
        quarter_year, quarter = years[i % len(years)], i % 4 + 1
        month_year, month = years[(i + 1) % len(years)], (i * 5) % 12 + 1
        day = date(years[(i + 2) % len(years)], (i * 7) % 12 + 1, (i * 3) % 28 + 1)
        periods_ = [
            (fee.GAS_YEAR, periods.gas_year_period(gas_years[i % len(gas_years)])),
            (fee.QUARTER, periods.quarter_period(quarter_year, quarter)),
            (fee.MONTH, (periods.month_first(month_year, month), periods.month_last(month_year, month))),
            (fee.DAY, (day, day)),
        ]
        for instrument, (start, end) in periods_:
            for unit, capacity in (("kWh/d", 50000), ("kWh/h", 1234.5)):
                cases.append(Case(booked, instrument, start, end, capacity, unit, rate_sets[i % len(rate_sets)]))
    return cases


@pytest.fixture(scope="module")
def real(tmp_path_factory) -> Checked:
    table = tariffs.load_tariffs(tariffs.DEFAULT_PATH).table
    catalog = points.build_catalog(table)
    today = date.today()
    q4 = periods.quarter_period(2026, 4)
    moson = find(catalog, "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)")
    named = [
        Case(moson, fee.QUARTER, *q4, rates={"HUF": 395.5}),
        Case(moson, fee.QUARTER, *q4),
        Case(single(catalog, "GCA", "Mosonmagyaróvár AT>HU"), fee.GAS_YEAR, *periods.gas_year_period(2026)),
        Case(single(catalog, "EUSTR", "Balassagyarmat SK>HU"), fee.GAS_YEAR, *periods.gas_year_period(2025)),
        Case(find(catalog, "Csanádpalota RO>HU (Transgaz + FGSZ)"), fee.QUARTER, *q4, rates={"HUF": 395.5}),
        Case(find(catalog, "Csanádpalota RO>HU (Transgaz + FGSZ)"), fee.QUARTER, *q4, rates={"HUF": 395.5, "RON": 4.97}),
        Case(find(catalog, "Kulata/Sidirokastron BG>GR (Bulgartransgaz + DESFA)"), fee.QUARTER, *q4),
        Case(single(catalog, "FGSZ", "Kiskundorozsma 2 HU>RS"), fee.QUARTER, *q4),
        Case(moson, fee.QUARTER, *q4, capacity=0),
        Case(moson, fee.QUARTER, *q4, capacity="abc"),
    ]
    cases = named + sweep_cases(table, catalog, today)
    gastrans = tariffs.TSO_NAMES["Gastran"]
    lists = ["dv_points", "dv_periods", "msg_main", "out1_total"]
    extra = [
        ({"in_booking": "Single side", "in_tso": gastrans}, lists),
        ({"in_booking": "LNG entry"}, lists),
        ({"in_booking": "Bundled", "in_point": moson.label(), "in_instrument": "Gas year", "in_period": "2026/27",
          "in_capacity": 50000}, lists),
        ({"in_instrument": "Quarter", "in_period": "2026 Q4"}, lists),
        ({"in_booking": "LNG entry"}, lists),  # the bundle label is left in the point cell
        ({"in_booking": "Bundled", "in_instrument": "Month"}, lists),  # "2026 Q4" is left in the period cell
        ({"in_instrument": "Day", "in_day": None}, lists),
    ]
    return Checked(table, "tariffs_real.xlsx", tmp_path_factory.mktemp("real"), cases, extra)


def test_every_point_agrees_with_the_app(real):
    found = real.all_differences()
    assert not found, f"{len(found)} difference(s):\n" + "\n".join(found[:40])


def test_bundle_figures_and_eur_total(real):
    got = real.got(0)
    assert got["out1_total"] == "2605.83" and got["out1_amounts"][:3] == ["868.61"] * 3
    assert got["out1_rounding"] == "Gas Connect Austria bills its tariff rounded to 4 decimals."
    assert got["out2_total"] == "782558" and got["out2_amounts"][:3] == ["260853", "260853", "260852"]
    assert got["out_eur_total"] == "4584.48"
    assert got["out_eur_caption"] == "Sum of both sides' totals, converted at 1 EUR = 395.5 HUF."


def test_rate_missing(real):
    got = real.got(1)
    assert got["out2_total"] == "782558" and got["out_eur_total"] == ""
    assert got["out_eur_msg"] == "Enter the HUF per EUR rate to see the EUR total."


def test_gas_year_across_a_tariff_change_in_equal_months(real):
    got = real.got(2)
    assert got["out1_price"] == "3.9700 / 4.1000" and got["out1_total"] == "8473.96"
    assert got["out1_amounts"] == ["689.24"] * 3 + ["711.81"] * 4 + ["711.80"] * 5


def test_repeated_tariff_shown_once(real):
    assert real.got(3)["out1_price"] == "8.7600 / 9.6360"


def test_two_rates_needed(real):
    assert real.got(4)["out_eur_msg"] == "Enter the RON per EUR rate to see the EUR total."
    assert real.got(5)["out_eur_total"] != "" and real.got(5)["out_eur_msg"] == ""


def test_both_sides_in_eur(real):
    got = real.got(6)
    assert got["out_eur_total"] != "" and got["out_eur_caption"] == "Sum of both sides' totals, both in EUR."


def test_interruptible_warning(real):
    assert real.got(7)["out1_interruptible"].startswith("This point has no Firm tariff")


def test_invalid_capacity(real):
    for i in (8, 9):
        got = real.got(i)
        assert got["msg_main"] == "Capacity must be a positive number." and got["out1_total"] == ""


def test_points_and_periods_follow_the_choices(real):
    gastrans, lng, gas_year, quarter, stale_point, stale_period, no_day = real.extra
    catalog = real.catalog
    assert gastrans["dv_points"] == [p.fee_label(catalog.capacity_type(p)) for p in catalog.singles_of("Gastran")]
    assert len(gastrans["dv_points"]) == 4
    assert lng["dv_points"] == [p.lng_label() for p in catalog.lng] and len(lng["dv_points"]) == 14
    moson = find(catalog, "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)")
    today = date.today()
    assert gas_year["dv_periods"] == [periods.gas_year_label(y) for y in fee.gas_year_choices(real.table, moson, today)]
    years = fee.calendar_year_choices(real.table, moson, today)
    assert quarter["dv_periods"] == [f"{y} Q{q}" for y in years for q in range(1, 5)]
    assert stale_point["msg_main"] == "Choose a point from the list." and stale_point["out1_total"] == ""
    assert stale_period["msg_main"] == "Choose a period from the list." and stale_period["out1_total"] == ""
    assert no_day["msg_main"] == "Choose a product period."


# --- the sample file and hand-made tables: the specs' worked figures -----------------------------------

@pytest.fixture(scope="module")
def sample(tmp_path_factory) -> Checked:
    table = tariffs.load_tariffs(tariffs.DEFAULT_SAMPLE_PATH).table
    catalog = points.build_catalog(table)
    q4 = periods.quarter_period(2026, 4)
    point = single(catalog, "FGSZ", "Kiskundorozsma 2 RS>HU")
    cases = [Case(point, fee.QUARTER, *q4), Case(point, fee.QUARTER, *q4, capacity=2000, unit="kWh/h")]
    return Checked(table, "tariffs_sample.xlsx", tmp_path_factory.mktemp("sample"), cases)


def test_sample_demo_quarter(sample):
    assert not sample.all_differences(), sample.all_differences()
    got = sample.got(0)
    assert got["out1_capacity"] == "2083.33" and got["out1_total"] == "1565115"
    assert got["out1_amounts"][:3] == ["521705"] * 3


def synthetic_table():
    eur = dict(currency="EUR", valid_from="2026-10-01", valid_to=None)
    return make_table(
        make_row(eic="TESTEIC00000001A", name="Alpha (AT>HU)", operator="GCA", direction="Exit", **eur,
                 prices={"Q4_Oct": 0.34148}),
        make_row(eic="TESTEIC00000002B", name="Beta (AT>SK)", operator="GCA", direction="Exit", **eur,
                 prices={"Q4_Oct": 100.0}),
        make_row(eic="TESTEIC00000003C", name="Gamma (RS>HU)", operator="Gastran", direction="Exit", **eur,
                 prices={"Q4_Oct": 92.0, "Year": 365.0}),
        make_row(eic="TESTEIC00000004D", name="Delta (BG>RS)", operator="BGTRGAZ", direction="Exit", unit="kWh/d",
                 **eur, prices={"Q4_Oct": 0.242217}),
        make_row(eic="TESTEIC00000005E", name="Epsilon (AT>HU)", operator="GCA", direction="Exit", **eur),
        make_row(eic="TESTEIC00000005E", name="Epsilon (AT>HU)", operator="FGSZ", direction="Entry",
                 valid_from="2027-01-01", valid_to=None),
    )


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory) -> Checked:
    table = synthetic_table()
    catalog = points.build_catalog(table)
    q4 = periods.quarter_period(2026, 4)
    by_name = {p.name: p for p in catalog.singles}
    cases = [
        Case(by_name["Alpha"], fee.QUARTER, *q4, capacity=500000, unit="kWh/h"),
        Case(by_name["Beta"], fee.QUARTER, *q4, capacity=1, unit="kWh/h"),
        Case(by_name["Gamma"], fee.QUARTER, *q4, capacity=1, unit="kWh/h"),
        Case(by_name["Gamma"], fee.GAS_YEAR, *periods.gas_year_period(2026), capacity=1, unit="kWh/h"),
        Case(by_name["Delta"], fee.QUARTER, *q4, capacity=50000),
        Case(by_name["Delta"], fee.QUARTER, *q4, capacity=1000, unit="kWh/h"),
        Case(catalog.bundles[0], fee.GAS_YEAR, *periods.gas_year_period(2026), rates={"HUF": 395.5}),
    ]
    return Checked(table, "hand-made", tmp_path_factory.mktemp("synthetic"), cases)


def test_hand_made_tables_agree_with_the_app(synthetic):
    found = synthetic.all_differences()
    assert not found, "\n".join(found)


def test_gas_connect_austria_rounds_the_tariff(synthetic):
    got = synthetic.got(0)
    assert got["out1_price"] == "0.3415" and got["out1_total"] == "170750.00"


def test_leftover_cents_go_to_the_first_months(synthetic):
    assert synthetic.got(1)["out1_amounts"][:3] == ["33.34", "33.33", "33.33"]


def test_gastrans_quarter_in_thirds_gas_year_by_days(synthetic):
    assert synthetic.got(2)["out1_amounts"][:3] == ["30.67", "30.67", "30.66"]
    assert synthetic.got(3)["out1_amounts"][:5] == ["31.00", "30.00", "31.00", "31.00", "28.00"]


def test_price_per_kwh_d(synthetic):
    assert synthetic.got(4)["out1_total"] == "12110.85"
    assert synthetic.got(4)["out1_amounts"][:3] == ["4080.83", "3949.19", "4080.83"]
    got = synthetic.got(5)
    assert got["out1_capacity"] == "24000.00" and got["out1_total"] == "5813.21"


def test_one_side_of_a_bundle_has_no_tariff(synthetic):
    got = synthetic.got(6)
    assert got["msg_main"] == "No tariff exists for the FGSZ entry side (Epsilon (AT>HU)) on 2026-10-01."
    assert got["out1_total"] == "" and got["out2_total"] == ""
