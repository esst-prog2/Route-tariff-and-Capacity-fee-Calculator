"""Runs the real Streamlit script headlessly against the synthetic sample."""

from datetime import date
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


def index_of(options, predicate):
    return next(i for i, p in enumerate(options) if predicate(p))


# --- 7.1 shell ---------------------------------------------------------------------------

def test_both_tabs_render_with_the_sample_loaded():
    at = start_app()
    assert [tab.label for tab in at.tabs] == ["Route Tariff Calculator", "Capacity Fee Calculator"]
    assert at.selectbox(key="route_tso").options == ["FGSZ"]
    assert at.selectbox(key="fee_tso").options == ["FGSZ"]
    assert "tariffs_sample.xlsx" in at.sidebar.caption[0].value


# --- 7.2 / 7.3 tab 1 --------------------------------------------------------------------------

def test_tab1_shows_huf_without_a_rate_and_eur_with_one_in_four_decimals():
    at = start_app()
    assert at.selectbox(key="route_entry").options == [p.route_label() for p in points.entries()]
    assert at.selectbox(key="route_exit").options == [p.route_label() for p in points.exits()]
    assert len(at.selectbox(key="route_entry").options) == 7 and len(at.selectbox(key="route_exit").options) == 5
    assert at.text_input(key="route_fx").value == ""  # starts blank

    segments, summary = frames(at)
    assert list(summary.columns) == ["", "HUF per kWh/h", "HUF/MWh"]  # no EUR column yet
    assert any("Enter today's HUF per EUR rate" in info.value for info in at.info)
    assert list(segments.columns) == ["Segment", "Product", "HUF per kWh/h", "Tariff used"]
    assert segments["Tariff used"].str.contains("entry from").all()
    assert summary[""].tolist() == ["Cheapest combination", "All daily", "Saving"]

    at.text_input(key="route_fx").set_value("400").run()
    assert not at.exception
    _, summary = frames(at)
    assert list(summary.columns) == ["", "HUF per kWh/h", "HUF/MWh", "EUR/MWh"]
    for value in summary["EUR/MWh"]:
        assert len(value.split(".")[1]) == 4
    assert any("at 1 EUR = 400 HUF" in caption.value for caption in at.caption)


def test_tab1_invalid_rate_shows_a_message_and_no_eur_column():
    at = start_app()
    at.text_input(key="route_fx").set_value("abc").run()
    assert any("positive number" in warning.value for warning in at.warning)
    assert "EUR/MWh" not in frames(at)[1].columns


def test_tab1_saving_equals_all_daily_minus_cheapest():
    at = start_app()
    _, summary = frames(at)
    cheapest, all_daily, saving = (float(v) for v in summary["HUF per kWh/h"])
    assert saving == pytest.approx(all_daily - cheapest, abs=1e-3)
    assert saving >= 0


def test_tab1_end_before_start_is_a_message():
    at = start_app()
    at.date_input(key="route_end").set_value(date(2026, 9, 1)).run()
    assert not at.exception
    assert any("invalid" in error.value for error in at.error)
    assert frames(at) == []


def test_tab1_same_physical_point_is_not_possible():
    at = start_app()
    entries, exits = points.entries(), points.exits()
    at.selectbox(key="route_entry").select_index(index_of(entries, lambda p: p.name == "Csanádpalota"))
    at.selectbox(key="route_exit").select_index(index_of(exits, lambda p: p.name == "Csanádpalota")).run()
    assert not at.exception
    assert any("not possible" in error.value for error in at.error)


def test_tab1_period_before_the_data_says_no_tariff():
    at = start_app()
    at.date_input(key="route_start").set_value(date(2010, 1, 1))
    at.date_input(key="route_end").set_value(date(2010, 1, 5)).run()
    assert not at.exception
    assert any("No tariff" in error.value for error in at.error)


# --- 7.4 tab 2 ----------------------------------------------------------------------------------------

def test_tab2_offers_twelve_unique_labels_and_four_instruments():
    at = start_app()
    labels = at.selectbox(key="fee_point").options
    assert len(labels) == 12 and len(set(labels)) == 12
    assert "Csanádpalota RO>HU (21Z000000000236Q)" in labels and "Csanádpalota HU>RO (21Z000000000236Q)" in labels
    assert at.selectbox(key="fee_instrument").options == ["Gas year", "Quarter", "Month", "Day"]


def test_tab2_demo_run_matches_the_hand_calculation():
    at = start_app()
    assert "positive number" in at.warning[0].value  # blank capacity: message, no result
    at.text_input(key="fee_capacity").set_value("50000").run()
    assert not at.exception
    assert at.selectbox(key="fee_point").value.fee_label().startswith("Kiskundorozsma 2 RS>HU")
    assert at.selectbox(key="fee_q_year").value == 2026 and at.selectbox(key="fee_quarter").value == 4
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Total cost (HUF)"] == "1,565,115"
    assert metrics["Capacity (kWh/h)"] == "2083.33"
    invoice = frames(at)[-1]
    assert invoice["Amount (HUF)"].tolist() == ["527,376", "510,363", "527,376", "1,565,115"]
    assert invoice["Month"].tolist() == ["2026-10", "2026-11", "2026-12", "Total"]


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
    entry, exit_ = points.entries()[0], points.exits()[0]
    make_frame(
        make_row(eic=entry.eic, direction="Entry", valid_from="2026-10-01", valid_to=None),
        make_row(eic=exit_.eic, direction="Exit", valid_from="2026-10-01", valid_to=None),
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
