"""Runs the real Streamlit script headlessly against the synthetic sample."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core import points, tariffs

from .helpers import corridor_points, make_frame, make_row

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def start_app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def frames(at):
    return [element.value for element in at.dataframe]


def route_line(at) -> str:
    return next(m.value for m in at.markdown if m.value.startswith("**Route:**")).removeprefix("**Route:** ")


def add_point(at, name):
    """Choose the next border point by name from the Next point list."""
    options = at.selectbox(key="route_next").options
    at.selectbox(key="route_next").select(next(o for o in options if o.startswith(name + " ("))).run()
    assert not at.exception, [e.value for e in at.exception]


def choose_route(at, begin, *names):
    at.selectbox(key="route_begin").select(begin).run()
    if not at.button(key="route_clear").disabled:  # same beginning: the route was not cleared
        at.button(key="route_clear").click().run()
    for name in names:
        add_point(at, name)


def start_single_side() -> AppTest:
    """The app with tab 2 switched to the Single side booking type."""
    at = start_app()
    at.radio(key="fee_booking").set_value("Single side").run()
    assert not at.exception, [e.value for e in at.exception]
    return at


# --- shell -----------------------------------------------------------------------------------

def test_both_tabs_render_with_the_sample_loaded():
    at = start_app()
    assert [tab.label for tab in at.tabs] == ["Route Tariff Calculator", "Capacity Fee Calculator"]
    assert at.radio(key="fee_booking").options == ["Bundled", "Single side", "LNG entry"]
    assert at.radio(key="fee_booking").value == "Bundled"
    assert "tariffs_sample.xlsx" in at.sidebar.caption[0].value


# --- tab 1 ------------------------------------------------------------------------------------

def test_tab1_has_a_beginning_dropdown_a_next_point_list_and_no_tso_dropdown():
    at = start_app()
    assert at.selectbox(key="route_begin").options == [
        "AT", "BG", "CR", "CZ", "DE", "GR", "HU", "IT", "NL", "PL", "RO", "RS", "SI", "SK", "UA"]
    assert at.selectbox(key="route_begin").value == "BG"
    assert route_line(at) == "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"
    assert not {"route_end_country", "route_tso", "route_entry", "route_exit"} & {s.key for s in at.selectbox}


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
    choose_route(at, "HU", "Kiskundorozsma 2", "Kireevo/Zaychar")
    point_table = frames(at)[0]
    assert point_table["Capacity type"].tolist() == ["Interruptible", "Interruptible", "Interruptible", "Firm"]
    assert any("Interruptible" in w.value and "interrupt it" in w.value for w in at.warning)


def test_tab1_is_one_point_table_with_products_and_eur_per_mwh():
    at = start_app()
    assert at.text_input(key="route_rate_HUF").value == ""  # starts blank
    tables = frames(at)
    assert len(tables) == 2  # points and details; no per-TSO tables, no summary, no route total without a rate
    point_table = tables[0]
    assert list(point_table.columns) == [
        "#", "TSO", "Point", "EIC", "Direction", "Capacity type", "Products", "EUR/MWh",
    ]
    assert point_table["Products"][1] == point_table["Products"][2]  # the two Gastrans points share products
    eur = point_table["EUR/MWh"].tolist()
    assert eur[3] == "" and all(value != "" for value in eur[:3])  # FGSZ waits for the rate
    assert any("Enter today's HUF per EUR rate" in info.value for info in at.info)
    assert not any(isinstance(c, str) and ("per kWh" in c or "HUF" in c) for t in tables for c in t.columns)

    at.text_input(key="route_rate_HUF").set_value("400").run()
    assert not at.exception
    point_table, route_total, _ = frames(at)
    assert route_total[""].tolist()[0] == "Cheapest combination"
    assert "All daily" not in route_total[""].tolist()
    for value in [*point_table["EUR/MWh"], *route_total["EUR/MWh"]]:
        assert len(value.split(".")[1]) == 4
    assert sum(Decimal(v) for v in point_table["EUR/MWh"]) == pytest.approx(
        Decimal(route_total["EUR/MWh"][0]), abs=Decimal("0.0003"))  # cells are rounded separately
    assert any("at 1 EUR = 400 HUF" in caption.value for caption in at.caption)


def test_tab1_route_without_hu_has_no_fx_box():
    at = start_app()
    at.button(key="route_remove_last").click().run()  # BG > Kireevo/Zaychar > RS
    assert not at.exception
    assert "route_rate_HUF" not in [t.key for t in at.text_input]
    point_table, route_total, _ = frames(at)
    assert "" not in point_table["EUR/MWh"].tolist()
    assert route_total[""].tolist()[0] == "Cheapest combination"


def test_tab1_invalid_rate_shows_a_message_and_no_route_total():
    at = start_app()
    at.text_input(key="route_rate_HUF").set_value("abc").run()
    assert any("positive number" in warning.value for warning in at.warning)
    assert len(frames(at)) == 2 and frames(at)[0]["EUR/MWh"].tolist()[3] == ""


def test_tab1_shows_over_booking_for_q4_minus_its_edge_days():
    at = start_app()
    assert not any("Over-booking" in info.value for info in at.info)  # the default period is exact quarters/months
    at.date_input(key="route_start").set_value(date(2026, 10, 2))
    at.date_input(key="route_end").set_value(date(2026, 12, 30)).run()
    assert not at.exception
    assert frames(at)[0]["Products"].tolist() == ["Q4 2026 (+2 days)"] * 4
    assert any("Over-booking" in info.value and "FGSZ 2 day(s)" in info.value for info in at.info)


def test_tab1_saving_is_against_the_next_shorter_products():
    at = start_app()
    at.text_input(key="route_rate_HUF").set_value("400").run()
    route_total = frames(at)[1]
    labels = route_total[""].tolist()
    assert labels[0] == "Cheapest combination" and labels[2] == "Saving"
    assert labels[1] in ("Without yearly products", "Without quarterly products", "Without monthly products",
                         "Next shorter products")
    cheapest, comparison, saving = (Decimal(v) for v in route_total["EUR/MWh"])
    assert saving == pytest.approx(comparison - cheapest, abs=Decimal("0.0002")) and saving >= 0


def test_tab1_daily_only_has_no_saving_line():
    at = start_app()
    at.text_input(key="route_rate_HUF").set_value("400")
    at.date_input(key="route_start").set_value(date(2026, 12, 1))
    at.date_input(key="route_end").set_value(date(2026, 12, 1)).run()
    assert not at.exception
    assert all(text.startswith("daily ") for text in frames(at)[0]["Products"])
    assert frames(at)[1][""].tolist() == ["Cheapest combination"]


def test_tab1_details_list_tariff_used_per_point_and_product():
    at = start_app()
    assert [e.label for e in at.expander] == ["Details"]
    assert not at.expander[0].proto.expanded  # closed until opened
    details = frames(at)[-1]
    assert list(details.columns) == ["TSO", "Point", "Direction", "Dates", "Product", "Tariff used", "Tariff"]
    assert set(details["Point"]) == set(frames(at)[0]["Point"])
    assert all(text.startswith("from ") for text in details["Tariff used"])
    units = {"FGSZ": " HUF per kWh/h", "Gastrans": " EUR per kWh/h", "Bulgartransgaz": " EUR per kWh/d"}
    for tso, product, tariff in zip(details["TSO"], details["Product"], details["Tariff"]):
        assert tariff.endswith(units[tso] + (" per day" if product == "daily" else ""))


def test_tab1_same_country_is_not_possible():
    at = start_app()
    add_point(at, "Kiskundorozsma 2")  # from HU back into RS
    assert any(w.value == "Not possible: the route would enter RS a second time." for w in at.warning)
    assert route_line(at) == "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"


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
    at = start_single_side()
    labels = at.selectbox(key="fee_point_FGSZ").options
    assert len(labels) == 14 and len(set(labels)) == 14
    assert "Csanádpalota RO>HU (21Z000000000236Q)" in labels and "Csanádpalota HU>RO (21Z000000000236Q)" in labels
    assert "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible" in labels
    assert "Mosonmagyaróvár HU>AT (21Z000000000003C) - Interruptible" in labels
    assert at.selectbox(key="fee_instrument").options == ["Gas year", "Quarter", "Month", "Day"]


def test_tab2_points_follow_the_tso():
    at = start_single_side()
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
    at = start_single_side()
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
    at = start_single_side()
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
    at = start_single_side()
    at.text_input(key="fee_capacity").set_value("50000")
    labels = at.selectbox(key="fee_point_FGSZ").options
    at.selectbox(key="fee_point_FGSZ").select_index(
        labels.index("Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible")).run()
    assert not at.exception
    assert any("Interruptible" in w.value for w in at.warning)


@pytest.mark.parametrize("instrument,lines", [("gas_year", 12 + 1), ("quarter", 3 + 1), ("month", 1 + 1), ("day", 1 + 1)])
def test_tab2_every_instrument_produces_an_invoice_that_sums_to_the_total(instrument, lines):
    at = start_single_side()
    at.text_input(key="fee_capacity").set_value("50000")
    at.selectbox(key="fee_instrument").select(instrument).run()
    assert not at.exception, [e.value for e in at.exception]
    invoice = frames(at)[-1]
    assert len(invoice) == lines
    amounts = [int(v.replace(",", "")) for v in invoice["Amount (HUF)"]]
    assert sum(amounts[:-1]) == amounts[-1]


def test_tab2_invalid_capacity_is_a_message():
    at = start_single_side()
    at.text_input(key="fee_capacity").set_value("abc").run()
    assert any("positive number" in w.value for w in at.warning)
    assert [m.label for m in at.metric] == []


def test_tab2_has_no_fx_input():
    at = start_single_side()
    assert [t.key for t in at.text_input] == ["route_rate_HUF", "fee_capacity"]


# --- tab 2 booking types and bundles (real tariff file) -------------------------------------------

@pytest.fixture
def real_app(monkeypatch):
    monkeypatch.setenv(tariffs.PATH_ENV_VAR, str(tariffs.DEFAULT_PATH))
    return start_app()


def test_tab2_booking_type_changes_the_dropdowns(real_app):
    at = real_app
    keys = lambda: {s.key for s in at.selectbox}
    assert "fee_bundle" in keys() and "fee_tso" not in keys()
    assert len(at.selectbox(key="fee_bundle").options) == 43
    at.radio(key="fee_booking").set_value("Single side").run()
    assert {"fee_tso", "fee_point_FGSZ"} <= keys() and "fee_bundle" not in keys()
    assert len(at.selectbox(key="fee_tso").options) == 21
    at.selectbox(key="fee_tso").select("BGTRGAZ").run()
    assert len(at.selectbox(key="fee_point_BGTRGAZ").options) == 13
    at.radio(key="fee_booking").set_value("LNG entry").run()
    assert not at.exception
    assert "fee_tso" not in keys() and len(at.selectbox(key="fee_lng").options) == 14


def test_tab2_bundle_shows_both_sides_and_waits_for_the_rate(real_app):
    at = real_app
    assert at.selectbox(key="fee_bundle").value.label() == "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)"
    at.text_input(key="fee_capacity").set_value("50,000").run()
    assert not at.exception, [e.value for e in at.exception]
    totals = [m.value for m in at.metric if m.label.startswith("Total cost")]
    assert totals == ["2,605.88", "782,558"]
    invoices = frames(at)[-2:]
    assert invoices[0]["Amount (EUR)"].tolist() == ["878.07", "849.74", "878.07", "2,605.88"]
    assert invoices[1]["Amount (HUF)"].tolist() == ["263,688", "255,182", "263,688", "782,558"]
    assert [t.key for t in at.text_input if t.key.startswith("fee_rate_")] == ["fee_rate_HUF"]
    assert any("HUF per EUR rate" in i.value for i in at.info)
    assert "Bundle total (EUR)" not in [m.label for m in at.metric]


def test_tab2_bundle_total_after_the_rate(real_app):
    at = real_app
    at.text_input(key="fee_capacity").set_value("50000").run()  # the rate box appears with a result
    at.text_input(key="fee_rate_HUF").set_value("395.5").run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Bundle total (EUR)"] == "4,584.53"
    assert any("at 1 EUR = 395.5 HUF" in c.value for c in at.caption)


def test_tab2_bundle_with_both_sides_in_eur_has_no_rate_box(real_app):
    at = real_app
    options = at.selectbox(key="fee_bundle").options
    at.selectbox(key="fee_bundle").select_index(
        options.index("Kulata/Sidirokastron BG>GR (Bulgartransgaz + DESFA)"))
    at.text_input(key="fee_capacity").set_value("50000").run()
    assert not at.exception
    assert not [t for t in at.text_input if t.key.startswith("fee_rate_")]
    assert "Bundle total (EUR)" in [m.label for m in at.metric]


def test_tab2_lng_entry_has_no_fx(real_app):
    at = real_app
    at.radio(key="fee_booking").set_value("LNG entry").run()
    at.text_input(key="fee_capacity").set_value("50000").run()
    assert not at.exception
    assert [t.key for t in at.text_input] == ["route_rate_HUF", "fee_capacity"]
    assert len([m for m in at.metric if m.label.startswith("Total cost")]) == 1


def test_tab2_gas_year_shows_both_tariffs_and_splits_the_invoice(real_app):
    at = real_app
    at.radio(key="fee_booking").set_value("Single side").run()
    at.selectbox(key="fee_tso").select("GCA").run()
    options = at.selectbox(key="fee_point_GCA").options
    at.selectbox(key="fee_point_GCA").select_index(options.index("Mosonmagyaróvár AT>HU (21Z000000000003C)"))
    at.selectbox(key="fee_instrument").select("gas_year").run()
    at.selectbox(key="fee_gas_year").select(2026)
    at.text_input(key="fee_capacity").set_value("50000").run()
    assert not at.exception, [e.value for e in at.exception]
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Price (Year, EUR per kWh/h)"] == "3.9700 / 4.1000"
    assert metrics["Total cost (EUR)"] == "8,473.40"
    assert any("from 2026-01-01 for 2026-10-01 to 2026-12-31" in c.value for c in at.caption)
    invoice = frames(at)[-1]
    assert invoice["Amount (EUR)"].tolist()[:4] == ["702.45", "679.79", "702.45", "725.46"]
    assert invoice["Amount (EUR)"].tolist()[-1] == "8,473.40"


def test_tab2_repeated_tariff_is_shown_once(real_app):
    at = real_app
    at.radio(key="fee_booking").set_value("Single side").run()
    at.selectbox(key="fee_tso").select("EUSTR").run()
    options = at.selectbox(key="fee_point_EUSTR").options
    at.selectbox(key="fee_point_EUSTR").select_index(options.index("Balassagyarmat SK>HU (21Z000000000358C)"))
    at.selectbox(key="fee_instrument").select("gas_year").run()
    at.selectbox(key="fee_gas_year").select(2025)
    at.text_input(key="fee_capacity").set_value("50000").run()
    assert not at.exception, [e.value for e in at.exception]
    assert {m.label: m.value for m in at.metric}["Price (Year, EUR per kWh/h)"] == "8.7600 / 9.6360"


def test_tab1_shows_the_route_map():
    at = start_app()
    charts = at.get("vega_lite_chart")
    assert len(charts) == 1


def test_tab1_next_point_follows_the_route():
    at = start_app()
    at.button(key="route_remove_last").click().run()
    assert route_line(at) == "BG > Kireevo/Zaychar > RS"
    assert at.selectbox(key="route_next").label == "Next point (from RS)"
    assert at.selectbox(key="route_next").options == ["Kireevo/Zaychar (BG - RS)", "Kiskundorozsma 2 (HU - RS)"]
    add_point(at, "Kiskundorozsma 2")
    assert route_line(at) == "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"
    assert at.selectbox(key="route_next").value is None  # ready for the next choice


def test_tab1_remove_last_and_clear():
    at = start_app()
    at.button(key="route_remove_last").click().run()
    assert route_line(at) == "BG > Kireevo/Zaychar > RS"
    at.button(key="route_clear").click().run()
    assert route_line(at) == "BG"
    assert any("first border point" in i.value for i in at.info)
    assert frames(at) == []


def test_tab1_changing_the_beginning_clears_the_route():
    at = start_app()
    at.selectbox(key="route_begin").select("HU").run()
    assert route_line(at) == "HU" and frames(at) == []
    assert at.selectbox(key="route_next").label == "Next point (from HU)"


def test_tab1_point_not_on_the_current_country_is_refused():
    at = start_app()
    at.selectbox(key="route_begin").select("BG").run()
    assert not any(o.startswith("Vyrava") for o in at.selectbox(key="route_next").options)  # not even offered


def test_tab1_several_currencies_on_a_route(real_app):
    at = real_app
    choose_route(at, "BG", "Ruse/Giurgiu", "Csanádpalota")
    assert route_line(at) == "BG > Ruse/Giurgiu > RO > Csanádpalota > HU"
    assert [t.key for t in at.text_input if t.key.startswith("route_rate_")] == ["route_rate_RON", "route_rate_HUF"]
    at.text_input(key="route_rate_RON").set_value("5").run()
    eur = frames(at)[0]["EUR/MWh"].tolist()
    assert eur[3] == "" and all(value != "" for value in eur[:3])
    assert any("Enter today's HUF per EUR rate" in i.value for i in at.info)
    at.text_input(key="route_rate_HUF").set_value("400").run()
    assert frames(at)[1][""].tolist()[0] == "Cheapest combination"
    assert any("at 1 EUR = 5 RON; at 1 EUR = 400 HUF" in c.value for c in at.caption)


def test_tab1_all_eur_route_has_no_rate_box(real_app):
    at = real_app
    choose_route(at, "AT", "Tarvisio/Arnoldstein")
    assert not [t for t in at.text_input if t.key.startswith("route_rate_")]
    assert frames(at)[1][""].tolist()[0] == "Cheapest combination"
    assert frames(at)[0]["TSO"].tolist() == ["Trans Austria Gasleitung", "Snam Rete Gas"]


def test_real_file_is_the_default_and_tab1_still_prices_bg_to_hu(monkeypatch):
    monkeypatch.delenv(tariffs.PATH_ENV_VAR)
    at = start_app()
    assert "tariffs_real.xlsx" in at.sidebar.caption[0].value
    point_table = frames(at)[0]
    assert point_table["TSO"].tolist() == ["Bulgartransgaz", "Gastrans", "Gastrans", "FGSZ"]
    assert not at.error


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
          for p in corridor_points("BG", "HU")],
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
