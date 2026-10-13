"""Runs the real Streamlit script headlessly against the synthetic sample."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core import points, tariffs

from .helpers import make_frame, make_row

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def start_app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def frames(at):
    return [element.value for element in at.dataframe]


# --- shell -----------------------------------------------------------------------------------

def test_both_tabs_render_with_the_sample_loaded():
    at = start_app()
    assert [tab.label for tab in at.tabs] == ["Route Tariff Calculator", "Capacity Fee Calculator"]
    assert at.selectbox(key="fee_tso").options == ["FGSZ", "Gastrans", "Bulgartransgaz"]
    assert "tariffs_sample.xlsx" in at.sidebar.caption[0].value


# --- tab 1 ------------------------------------------------------------------------------------

def test_tab1_has_route_dropdowns_and_no_tso_dropdown():
    at = start_app()
    assert at.selectbox(key="route_begin").options == ["HU", "RS", "BG"]
    assert at.selectbox(key="route_end_country").options == ["HU", "RS", "BG"]
    assert (at.selectbox(key="route_begin").value, at.selectbox(key="route_end_country").value) == ("BG", "HU")
    assert not {"route_tso", "route_entry", "route_exit"} & {s.key for s in at.selectbox}


def test_tab1_lists_the_bg_to_hu_points_in_route_order():
    at = start_app()
    point_table = frames(at)[0]
    assert point_table["TSO"].tolist() == ["Bulgartransgaz", "Gastrans", "Gastrans", "FGSZ"]
    assert point_table["Point"].tolist() == [
        "Kireevo/Zaychar (BG>RS)", "Kireevo/Zaychar (BG>RS)", "Kiskundorozsma 2 (RS>HU)", "Kiskundorozsma 2 (RS>HU)",
    ]
    assert point_table["Direction"].tolist() == ["Exit", "Entry", "Exit", "Entry"]
    assert point_table["Capacity type"].tolist() == ["Firm"] * 4
    assert not any("Interruptible" in w.value for w in at.warning)


def test_tab1_flags_interruptible_points_on_hu_to_bg():
    at = start_app()
    at.selectbox(key="route_begin").select("HU")
    at.selectbox(key="route_end_country").select("BG").run()
    assert not at.exception
    point_table = frames(at)[0]
    assert point_table["Capacity type"].tolist() == ["Interruptible", "Interruptible", "Interruptible", "Firm"]
    assert any("Interruptible" in w.value and "interrupt it" in w.value for w in at.warning)


def test_tab1_shows_own_units_and_eur_only_once_a_rate_is_entered():
    at = start_app()
    assert at.text_input(key="route_fx").value == ""  # starts blank
    tables = frames(at)
    assert len(tables) == 5  # points, three TSO segment tables, summary (no route total yet)
    assert "EUR per kWh/d" in tables[1].columns and "EUR per kWh/h" in tables[2].columns
    assert list(tables[3].columns) == ["Segment", "Product", "HUF per kWh/h", "Days outside period", "Tariff used"]
    summary = tables[4]
    assert summary["TSO"].tolist() == ["Bulgartransgaz", "Gastrans", "FGSZ"]
    assert summary["EUR/MWh"].tolist()[2] == "" and summary["EUR/MWh"].tolist()[0] != ""
    assert summary["Per MWh"].tolist()[2].endswith("HUF/MWh")
    assert any("Enter today's HUF per EUR rate" in info.value for info in at.info)

    at.text_input(key="route_fx").set_value("400").run()
    assert not at.exception
    tables = frames(at)
    route_total = tables[5]
    assert route_total[""].tolist() == ["Cheapest combination", "All daily", "Saving"]
    for value in [*tables[4]["EUR/MWh"], *route_total["EUR/MWh"]]:
        assert len(value.split(".")[1]) == 4
    assert any("at 1 EUR = 400 HUF" in caption.value for caption in at.caption)


def test_tab1_route_without_hu_has_no_fx_box():
    at = start_app()
    at.selectbox(key="route_end_country").select("RS").run()
    assert not at.exception
    assert "route_fx" not in [t.key for t in at.text_input]
    assert frames(at)[-1][""].tolist() == ["Cheapest combination", "All daily", "Saving"]


def test_tab1_invalid_rate_shows_a_message_and_no_route_total():
    at = start_app()
    at.text_input(key="route_fx").set_value("abc").run()
    assert any("positive number" in warning.value for warning in at.warning)
    assert len(frames(at)) == 5


def test_tab1_shows_over_booking_for_q4_minus_its_edge_days():
    at = start_app()
    assert not any("Over-booking" in info.value for info in at.info)  # the default period is exact quarters/months
    at.date_input(key="route_start").set_value(date(2026, 10, 2))
    at.date_input(key="route_end").set_value(date(2026, 12, 30)).run()
    assert not at.exception
    fgsz_segments = frames(at)[3]
    assert fgsz_segments["Product"].tolist() == ["quarterly"]
    assert fgsz_segments["Segment"].tolist() == ["2026-10-01 to 2026-12-31"]
    assert fgsz_segments["Days outside period"].tolist() == [2]
    assert any("Over-booking" in info.value and "FGSZ 2 day(s)" in info.value for info in at.info)


def test_tab1_saving_equals_all_daily_minus_cheapest():
    at = start_app()
    at.text_input(key="route_fx").set_value("400").run()
    summary, route_total = frames(at)[4:6]
    for cheapest, all_daily, saving in zip(summary["Cheapest"], summary["All daily"], summary["Saving"]):
        assert float(saving) == pytest.approx(float(all_daily) - float(cheapest), abs=1e-3)
    cheapest, all_daily, saving = (float(v) for v in route_total["EUR/MWh"])
    assert saving == pytest.approx(all_daily - cheapest, abs=1e-3) and saving >= 0


def test_tab1_same_country_is_not_possible():
    at = start_app()
    at.selectbox(key="route_begin").select("HU")
    at.selectbox(key="route_end_country").select("HU").run()
    assert not at.exception
    assert any("not possible" in error.value for error in at.error)
    assert "route_fx" not in [t.key for t in at.text_input]


def test_tab1_end_before_start_is_a_message():
    at = start_app()
    at.date_input(key="route_end").set_value(date(2026, 9, 1)).run()
    assert not at.exception
    assert any("invalid" in error.value for error in at.error)
    assert frames(at) == []


def test_tab1_period_before_the_bulgartransgaz_eur_rows_says_no_tariff():
    at = start_app()
    at.date_input(key="route_start").set_value(date(2025, 12, 1))
    at.date_input(key="route_end").set_value(date(2026, 1, 15)).run()
    assert not at.exception
    assert any("No tariff" in e.value and "Bulgartransgaz Kireevo/Zaychar (BG>RS)" in e.value for e in at.error)


# --- tab 2 ----------------------------------------------------------------------------------------

def test_tab2_offers_the_selected_tsos_points_and_four_instruments():
    at = start_app()
    labels = at.selectbox(key="fee_point_FGSZ").options
    assert len(labels) == 13 and len(set(labels)) == 13
    assert "Csanádpalota RO>HU (21Z000000000236Q)" in labels and "Csanádpalota HU>RO (21Z000000000236Q)" in labels
    assert "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible" in labels
    assert at.selectbox(key="fee_instrument").options == ["Gas year", "Quarter", "Month", "Day"]


def test_tab2_points_follow_the_tso():
    at = start_app()
    at.selectbox(key="fee_tso").select("Gastran").run()
    assert not at.exception
    labels = at.selectbox(key="fee_point_Gastran").options
    assert len(labels) == 4
    assert [label for label in labels if label.endswith(" - Interruptible")] == [
        "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible",
        "Kireevo/Zaychar RS>BG (58Z-000000007-KZ) - Interruptible",
    ]
    at.selectbox(key="fee_tso").select("BGTRGAZ").run()
    assert len(at.selectbox(key="fee_point_BGTRGAZ").options) == 13


def test_tab2_demo_run_matches_the_hand_calculation():
    at = start_app()
    assert "positive number" in at.warning[0].value  # blank capacity: message, no result
    at.text_input(key="fee_capacity").set_value("50000").run()
    assert not at.exception
    assert at.selectbox(key="fee_point_FGSZ").value.fee_label().startswith("Kiskundorozsma 2 RS>HU")
    assert at.selectbox(key="fee_q_year").value == 2026 and at.selectbox(key="fee_quarter").value == 4
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Total cost (HUF)"] == "1,565,115"
    assert metrics["Capacity (kWh/h)"] == "2083.33"
    invoice = frames(at)[-1]
    assert invoice["Amount (HUF)"].tolist() == ["527,376", "510,363", "527,376", "1,565,115"]
    assert invoice["Month"].tolist() == ["2026-10", "2026-11", "2026-12", "Total"]


def test_tab2_labels_follow_the_currency_and_unit():
    at = start_app()
    at.text_input(key="fee_capacity").set_value("50000")
    at.selectbox(key="fee_tso").select("BGTRGAZ").run()
    labels = at.selectbox(key="fee_point_BGTRGAZ").options
    at.selectbox(key="fee_point_BGTRGAZ").select_index(labels.index("Kireevo/Zaychar BG>RS (58Z-000000007-KZ)")).run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Capacity (kWh/d)"] == "50000.00"
    assert metrics["Total cost (EUR)"] == "12,110.87"
    invoice = frames(at)[-1]
    amounts = [Decimal(v.replace(",", "")) for v in invoice["Amount (EUR)"]]
    assert sum(amounts[:-1]) == amounts[-1]
    assert any("rounded to cents" in c.value for c in at.caption)


def test_tab2_interruptible_point_says_so():
    at = start_app()
    at.text_input(key="fee_capacity").set_value("50000")
    labels = at.selectbox(key="fee_point_FGSZ").options
    at.selectbox(key="fee_point_FGSZ").select_index(
        labels.index("Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible")).run()
    assert not at.exception
    assert any("Interruptible" in w.value for w in at.warning)


@pytest.mark.parametrize("instrument,lines", [("gas_year", 12 + 1), ("quarter", 3 + 1), ("month", 1 + 1), ("day", 1 + 1)])
def test_tab2_every_instrument_produces_an_invoice_that_sums_to_the_total(instrument, lines):
    at = start_app()
    at.text_input(key="fee_capacity").set_value("50000")
    at.selectbox(key="fee_instrument").select(instrument).run()
    assert not at.exception, [e.value for e in at.exception]
    invoice = frames(at)[-1]
    assert len(invoice) == lines
    amounts = [int(v.replace(",", "")) for v in invoice["Amount (HUF)"]]
    assert sum(amounts[:-1]) == amounts[-1]


def test_tab2_invalid_capacity_is_a_message():
    at = start_app()
    at.text_input(key="fee_capacity").set_value("abc").run()
    assert any("positive number" in w.value for w in at.warning)
    assert [m.label for m in at.metric] == []


def test_tab2_has_no_fx_input():
    at = start_app()
    assert [t.key for t in at.text_input] == ["route_fx", "fee_capacity"]


# --- 7.5 validation messages ------------------------------------------------------------------------------

def test_a_file_without_a_required_column_shows_a_plain_message(tmp_path, monkeypatch):
    broken = tmp_path / "broken.xlsx"
    make_frame(make_row()).drop(columns=["Q1_Jan"]).to_excel(broken, sheet_name="Capacity_fee", index=False)
    monkeypatch.setenv(tariffs.PATH_ENV_VAR, str(broken))
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    assert any("Q1_Jan" in error.value for error in at.error)
    assert len(at.tabs) == 0  # nothing to calculate with


def test_excluded_rows_are_reported_but_the_app_still_works(tmp_path, monkeypatch):
    path = tmp_path / "partial.xlsx"
    formats = {"FGSZ": {}, "Gastran": {"currency": "EUR"}, "BGTRGAZ": {"currency": "EUR", "unit": "kWh/d"}}
    make_frame(
        *[make_row(eic=p.eic, direction=p.direction, operator=p.tso, valid_from="2026-10-01", valid_to=None,
                   **formats[p.tso])
          for p in points.route_points("BG", "HU")],
        make_row(eic="BADROW", name="Bad", prices={"D_Dec": None}),
    ).to_excel(path, sheet_name="Capacity_fee", index=False)
    monkeypatch.setenv(tariffs.PATH_ENV_VAR, str(path))
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("excluded" in expander.label for expander in at.sidebar.expander)
    assert len(at.tabs) == 2


def test_missing_configured_file_is_a_message(tmp_path, monkeypatch):
    monkeypatch.setenv(tariffs.PATH_ENV_VAR, str(tmp_path / "nope.xlsx"))
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    assert any("not found" in error.value for error in at.error)
