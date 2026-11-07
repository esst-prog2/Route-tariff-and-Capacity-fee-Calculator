"""Streamlit front end. All business rules live in `core/`; this file only
collects inputs and formats results."""

from __future__ import annotations

import json
import os
from datetime import date
from fractions import Fraction

import altair as alt
import pandas as pd
import streamlit as st

from core import fee, guarantee, map_points, money, periods, points
from core.labels import products_text
from core.points import Bundle
from core.fee import dates_text
from core.route import FIRST_POINT_MESSAGE, RouteError, calculate_route, point_tariff, point_tariff_used
from core.tariffs import INTERRUPTIBLE, TSO_FORMATS, LoadResult, load_tariffs, resolve_tariff_path

st.set_page_config(page_title="Route Tariff and Capacity Fee Calculator", layout="wide")

QUARTER_MONTHS = {1: "Jan-Mar", 2: "Apr-Jun", 3: "Jul-Sep", 4: "Oct-Dec"}


# --- data loading (cached per file contents / modification time) -------------------

@st.cache_data(show_spinner=False)
def _load_path(path: str, modified: float) -> LoadResult:
    return load_tariffs(path)


@st.cache_data(show_spinner=False)
def _load_bytes(data: bytes) -> LoadResult:
    import io

    return load_tariffs(io.BytesIO(data))


def load_data() -> tuple[LoadResult, str]:
    """The uploaded file if there is one, else the configured file."""
    uploaded = st.sidebar.file_uploader(
        "Tariff file (optional)", type=["xlsx"],
        help="Replaces the configured tariff file for this session only.",
    )
    if uploaded is not None:
        return _load_bytes(uploaded.getvalue()), f"Uploaded file: {uploaded.name}"
    path = resolve_tariff_path()
    if not path.exists():
        return LoadResult(None, [f"The tariff file was not found: {path}"]), f"Configured file: {path}"
    return _load_path(str(path), os.path.getmtime(path)), f"Configured file: {path.name}"


# --- formatting helpers ------------------------------------------------------------------

def dec4(value: Fraction | None) -> str:
    return "" if value is None else money.format_decimal(value, 4)


def plain_rate(rate: Fraction) -> str:
    text = money.format_decimal(rate, 4)
    return text.rstrip("0").rstrip(".") if "." in text else text


def tariff_text(leg, prices: tuple[Fraction, ...], product: str) -> str:
    """Exact tariff cell(s) in the leg's own unit, e.g. "0.1211087 EUR per kWh/d"."""
    unit = f"{leg.currency} per {leg.unit}" + (" per day" if product == "daily" else "")
    return ", ".join(money.format_exact(price) for price in prices) + f" {unit}"


def rates_text(rates) -> str:
    """The typed rates as shown under a EUR figure: "at 1 EUR = 5 RON; at 1 EUR = 400 HUF"."""
    return "; ".join(f"at 1 EUR = {plain_rate(rate)} {currency}" for currency, rate in rates)


# --- tab 1 -----------------------------------------------------------------------------------

MAP_HEIGHT = 750
DEFAULT_BEGIN = "BG"
DEFAULT_ROUTE = ("Kireevo/Zaychar", "Kiskundorozsma 2")  # BG > RS > HU


@st.cache_data(show_spinner=False)
def _countries_geojson() -> dict:
    return json.loads(map_points.COUNTRIES_GEOJSON.read_text(encoding="utf-8"))


def init_route(network: points.Network) -> None:
    """The route lives in session state; it starts as the default BG > RS > HU route."""
    if "route_points" in st.session_state:
        return
    names = {p.name: p.label for p in network.points}
    route = [names[name] for name in DEFAULT_ROUTE if name in names]
    st.session_state.route_points = route if len(route) == len(DEFAULT_ROUTE) else []
    st.session_state.route_map_version = 0
    st.session_state.route_message = None


def add_route_point(network: points.Network, label: str) -> None:
    """Add a point (from a map click or the Next point list), or keep the reason it cannot be added."""
    begin = st.session_state.route_begin
    try:
        st.session_state.route_points = points.extend_route(network, begin, st.session_state.route_points, label)
        st.session_state.route_message = None
    except points.RouteNotPossible as refused:
        st.session_state.route_message = str(refused)
    st.session_state.route_map_version += 1  # a new map key starts with an empty selection


def _next_point_chosen(network: points.Network) -> None:
    label = st.session_state.route_next
    if label:
        add_route_point(network, label)
    st.session_state.route_next = None


def _remove_last() -> None:
    st.session_state.route_points = st.session_state.route_points[:-1]
    st.session_state.route_message = None


def _clear_route() -> None:
    st.session_state.route_points = []
    st.session_state.route_message = None


def route_map(network: points.Network, labels: list[str]) -> alt.LayerChart:
    """Borders only, each country's code in its middle, a marker per border point; the route's
    markers are highlighted and joined in order. Clicking a marker selects its label."""
    countries = alt.Chart(alt.InlineData(values=_countries_geojson(), format=alt.DataFormat(property="features"))).mark_geoshape(
        fill="transparent", stroke="#8a8a8a", strokeWidth=0.8, clip=True)
    codes = pd.DataFrame([{"code": c, "lon": x, "lat": y} for c, (x, y) in map_points.COUNTRY_LABELS.items()
                          if c in network.countries])
    code_text = alt.Chart(codes).mark_text(fontSize=13, fontWeight="bold", color="#555555").encode(
        longitude="lon:Q", latitude="lat:Q", text="code:N")

    on_route = {label: i for i, label in enumerate(labels)}
    rows = []
    for point in network.points:
        position = map_points.point_position(point.name, point.countries)
        if position is not None:  # the others are listed under the map (`unplaced_points`)
            rows.append({"label": point.label, "name": point.name, "between": f"{point.countries[0]} - {point.countries[1]}",
                         "lon": position[0], "lat": position[1], "on_route": point.label in on_route,
                         "order": on_route.get(point.label, -1)})
    markers = pd.DataFrame(rows)
    pick = alt.selection_point(name="pick", fields=["label"], on="click", clear=False)
    dots = alt.Chart(markers).mark_circle(size=140, stroke="white", strokeWidth=1).encode(
        longitude="lon:Q", latitude="lat:Q",
        color=alt.condition("datum.on_route", alt.value("#d62728"), alt.value("#1f77b4")),
        tooltip=[alt.Tooltip("name:N", title="Point"), alt.Tooltip("between:N", title="Between")],
    ).add_params(pick)
    line = alt.Chart(markers[markers["on_route"]]).mark_line(color="#d62728", strokeWidth=2).encode(
        longitude="lon:Q", latitude="lat:Q", order="order:Q")
    # Zoom to the border points and country labels (not to whole countries, which would shrink the
    # map to fit eastern Ukraine), so the markers stay apart; borders beyond the frame are cut.
    return (countries + line + dots + code_text).project(type="mercator", fit=map_points.map_frame()).properties(
        height=MAP_HEIGHT)


def unplaced_points(network: points.Network) -> list[str]:
    """Map points without a typed-in position (possible with an uploaded file): no marker is drawn for them."""
    return [p.label for p in network.points if map_points.point_position(p.name, p.countries) is None]


def route_tab(table, network: points.Network) -> None:
    init_route(network)
    countries = list(network.countries)
    begin = st.selectbox("Route beginning", countries,
                         index=countries.index(DEFAULT_BEGIN) if DEFAULT_BEGIN in countries else 0,
                         key="route_begin", on_change=_clear_route)
    route_labels = st.session_state.route_points

    if st.session_state.route_message:
        st.warning(st.session_state.route_message)
        st.session_state.route_message = None

    event = st.altair_chart(route_map(network, route_labels), on_select="rerun", width="stretch",
                            key=f"route_map_{st.session_state.route_map_version}")
    unplaced = unplaced_points(network)
    if unplaced:
        st.caption(f"Not on the map (no position known), choose them in the Next point list: {', '.join(unplaced)}.")
    picked = event.selection.get("pick") if event and event.selection else None
    if picked:
        add_route_point(network, picked[0]["label"])
        st.rerun()

    current = points.route_end(network, begin, route_labels)
    left, middle, right = st.columns([3, 1, 1], vertical_alignment="bottom")
    left.selectbox(f"Next point (from {current})", [p.label for p in network.points_from(current)], index=None,
                   placeholder="Choose a border point", key="route_next", on_change=_next_point_chosen, args=(network,))
    middle.button("Remove last", on_click=_remove_last, disabled=not route_labels, key="route_remove_last", width="stretch")
    right.button("Clear", on_click=_clear_route, disabled=not route_labels, key="route_clear", width="stretch")
    st.markdown(f"**Route:** {points.route_text(network, begin, route_labels)}")

    left, right = st.columns(2)
    start = left.date_input("Booking start (inclusive)", value=date(2026, 10, 1), min_value=date(2000, 1, 1),
                            max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="route_start")
    end = right.date_input("Booking end (inclusive)", value=date(2027, 3, 31), min_value=date(2000, 1, 1),
                           max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="route_end")

    currencies = list(dict.fromkeys(
        TSO_FORMATS[p.tso][0] for p in points.route_crossing_points(network, begin, route_labels)
        if TSO_FORMATS[p.tso][0] != "EUR"))
    rate_texts = {}
    for column, currency in zip(st.columns(max(len(currencies), 1)), currencies):
        rate_texts[currency] = column.text_input(
            f"{currency} per 1 EUR", value="", placeholder="e.g. 400" if currency == "HUF" else "",
            key=f"route_rate_{currency}", help="Type today's rate. EUR figures in this currency appear once it is entered.")

    result = calculate_route(table, begin, route_labels, start, end, rate_texts, network)
    if isinstance(result, RouteError):
        (st.info if result.message == FIRST_POINT_MESSAGE else st.error)(result.message)
        return

    st.subheader(result.route_text)
    st.caption(f"Booking period {dates_text(start, end)} ({result.days} days), hub to hub.")

    st.markdown("**Network points on the route**")
    capacity_types = [table.capacity_type(*p.key) for p in result.points]
    by_point = {p: (leg, i) for leg in result.legs for i, p in enumerate(leg.points)}
    st.dataframe(
        pd.DataFrame(
            {
                "#": list(range(1, len(result.points) + 1)),
                "TSO": [p.tso_name for p in result.points],
                "Point": [p.cleaned_name for p in result.points],
                "EIC": [p.eic for p in result.points],
                "Direction": [p.direction for p in result.points],
                "Capacity type": capacity_types,
                "Products": [products_text(by_point[p][0].plan) for p in result.points],
                "EUR/MWh": [dec4(by_point[p][0].point_eur_per_mwh[by_point[p][1]]) for p in result.points],
            }
        ),
        hide_index=True, width="stretch",
    )
    if INTERRUPTIBLE in capacity_types:
        st.warning("Interruptible capacity is used where a point has no Firm tariff; "
                   "the TSO can interrupt it.")

    over_booked = [f"{leg.tso_name} {leg.plan.days_outside} day(s)" for leg in result.legs if leg.plan.days_outside]
    if over_booked:
        st.info(f"Over-booking: {', '.join(over_booked)} outside the booking period, because a longer product "
                "costs less than covering only the booked days. Per-MWh figures use the booked days only.")

    if result.eur_per_mwh is not None:
        st.markdown("**Route total (EUR/MWh)**")
        labels, values = ["Cheapest combination"], [dec4(result.eur_per_mwh)]
        if result.comparison_label:
            labels += [result.comparison_label, "Saving"]
            values += [dec4(result.comparison_eur_per_mwh), dec4(result.comparison_saving_eur_per_mwh)]
        st.dataframe(pd.DataFrame({"": labels, "EUR/MWh": values}), hide_index=True, width="stretch")
        if result.comparison_note:
            st.caption(f"Compared per TSO: {result.comparison_note}.")
        note = "Per-MWh figures assume the booked capacity is used fully on the booked days."
        if result.rates_used:
            note = f"EUR/MWh {rates_text(result.rates_used)}. " + note
        st.caption(note)
    else:
        for currency in result.invalid_rates:
            st.warning(money.rate_message(currency))
        if result.missing_rates:
            names = " and ".join(f"{c} per EUR" for c in result.missing_rates)
            plural = "s" if len(result.missing_rates) > 1 else ""
            st.info(f"Enter today's {names} rate{plural} to see every point's and the route's EUR/MWh.")

    with st.expander("Details", expanded=False):
        details = [
            (p.tso_name, p.cleaned_name, p.direction, dates_text(seg.start, seg.end), seg.product,
             point_tariff_used(table, p, seg), tariff_text(by_point[p][0], point_tariff(table, p, seg), seg.product))
            for p in result.points for seg in by_point[p][0].plan.segments
        ]
        st.dataframe(
            pd.DataFrame(details, columns=["TSO", "Point", "Direction", "Dates", "Product", "Tariff used", "Tariff"]),
            hide_index=True, width="stretch",
        )


# --- tab 2 -----------------------------------------------------------------------------------

BUNDLED, SINGLE_SIDE, LNG_ENTRY = "Bundled", "Single side", "LNG entry"
DEFAULT_BUNDLE = "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)"


def choose_booking(catalog: points.Catalog):
    """The booking-type radio and the matching point dropdown(s); each type and
    TSO has its own widget key, so a switch never keeps a point of the wrong kind."""
    booking = st.radio("Booking type", (BUNDLED, SINGLE_SIDE, LNG_ENTRY), horizontal=True, key="fee_booking")
    if booking == BUNDLED:
        labels = [b.label() for b in catalog.bundles]
        default = labels.index(DEFAULT_BUNDLE) if DEFAULT_BUNDLE in labels else 0
        options = catalog.bundles
        return options and st.selectbox("Bundled point", options, index=default, format_func=Bundle.label,
                                        key="fee_bundle")
    if booking == LNG_ENTRY:
        options = catalog.lng
        return options and st.selectbox("LNG terminal", options, format_func=points.Point.lng_label, key="fee_lng")
    tsos = catalog.tsos()
    if not tsos:
        return None
    tso = st.selectbox("TSO", tsos, index=tsos.index(points.FGSZ) if points.FGSZ in tsos else 0,
                       format_func=points.tso_name, key="fee_tso")
    tso_points = catalog.singles_of(tso)
    default_point = next((i for i, p in enumerate(tso_points) if p.name == "Kiskundorozsma 2"), 0)
    return st.selectbox("Network point", tso_points, index=default_point,
                        format_func=lambda p: p.fee_label(catalog.capacity_type(p)), key=f"fee_point_{tso}")


def show_side(result: fee.FeeResult, invoice_title: str) -> None:
    """Capacity, price, total and monthly invoice of one point, in its own currency."""
    currency = result.currency
    left, middle, right = st.columns(3)
    left.metric(f"Capacity ({result.unit})", money.format_decimal(result.capacity, 2))
    # Every distinct tariff the product is priced from, once each, in date order.
    prices = " / ".join(dec4(price) for price in dict.fromkeys(result.part_prices)) or dec4(result.price)
    middle.metric(f"Price ({result.price_column}, {currency} per {result.unit})", prices)
    right.metric(f"Total cost ({currency})", money.format_amount(result.total, currency))
    rounding = "whole forints" if money.CURRENCY_DECIMALS[currency] == 0 else "cents"
    rounded = (f" {result.point.tso_name} bills its tariff rounded to {result.tariff_decimals} decimals."
               if result.tariff_decimals is not None else "")
    st.caption(f"Tariff used: {result.tariff_used}.{rounded} "
               f"All amounts are in {currency}; the total is rounded to {rounding}.")
    if result.capacity_type == INTERRUPTIBLE:
        st.warning("This point has no Firm tariff, so Interruptible capacity is priced; the TSO can interrupt it.")

    lines = [(f"{line.year}-{line.month:02d}", line.days, money.format_amount(line.amount, currency))
             for line in result.invoice]
    lines.append(("Total", sum(line.days for line in result.invoice), money.format_amount(result.total, currency)))
    st.markdown(f"**{invoice_title}**")
    if result.equal_months:
        share = "1/12 of the gas year" if result.instrument == fee.GAS_YEAR else "1/3 of the quarter"
        st.caption(f"{result.point.tso_name} invoices each month as {share} at the tariff valid in it, "
                   "whatever the month's number of days.")
    st.dataframe(pd.DataFrame(lines, columns=["Month", "Days", f"Amount ({currency})"]), hide_index=True, width="stretch")


def show_bundle_total(result: fee.BundleFeeResult) -> None:
    """Rate boxes for the sides not in EUR, then the bundle's EUR total or what is missing."""
    rate_texts = {}
    for currency in result.rate_currencies:
        rate_texts[currency] = st.text_input(f"{currency} per 1 EUR", value="", placeholder="e.g. 395.5",
                                             key=f"fee_rate_{currency}")
    total = fee.bundle_eur_total(result, rate_texts)
    if isinstance(total, fee.RatesNeeded):
        st.info(total.message)
        return
    st.metric("Bundle total (EUR)", money.format_amount(total.amount, "EUR"))
    rates = rates_text(total.rates)
    st.caption("Sum of both sides' totals" + (f", converted {rates}." if rates else ", both in EUR."))


def choose_product(table, booked, today: date, prefix: str) -> tuple[str, dict]:
    """The product instrument and its period pickers (tabs 2 and 3, each with its own key prefix);
    returns the instrument and the selection for `fee.resolve_period`."""
    instrument = st.selectbox("Product instrument", fee.INSTRUMENTS, index=fee.INSTRUMENTS.index(fee.QUARTER),
                              format_func=fee.INSTRUMENT_LABELS.get, key=f"{prefix}_instrument")

    gas_years = fee.gas_year_choices(table, booked, today)
    calendar_years = fee.calendar_year_choices(table, booked, today)
    year_default = calendar_years.index(2026) if 2026 in calendar_years else 0

    selection: dict = {}
    if instrument == fee.GAS_YEAR:
        current = periods.gas_year_start_year(today)
        selection["gas_year"] = st.selectbox(
            "Gas year", gas_years, index=gas_years.index(current) if current in gas_years else 0,
            format_func=periods.gas_year_label, key=f"{prefix}_gas_year")
    elif instrument == fee.QUARTER:
        left, right = st.columns(2)
        selection["year"] = left.selectbox("Year", calendar_years, index=year_default, key=f"{prefix}_q_year")
        selection["quarter"] = right.selectbox("Quarter", [1, 2, 3, 4], index=3,
                                               format_func=lambda q: f"Q{q} ({QUARTER_MONTHS[q]})",
                                               key=f"{prefix}_quarter")
    elif instrument == fee.MONTH:
        left, right = st.columns(2)
        selection["year"] = left.selectbox("Year", calendar_years, index=year_default, key=f"{prefix}_m_year")
        selection["month"] = right.selectbox("Month", list(range(1, 13)), format_func=lambda m: f"{m:02d}",
                                             key=f"{prefix}_month")
    else:
        selection["day"] = st.date_input("Day", value=date(2026, 12, 5), min_value=date(2000, 1, 1),
                                         max_value=date(2100, 12, 31), format="YYYY-MM-DD", key=f"{prefix}_day")
    return instrument, selection


def choose_capacity(prefix: str) -> tuple[str, str]:
    """The requested capacity box and its unit dropdown (tabs 2 and 3)."""
    left, right = st.columns([3, 1])
    capacity = left.text_input("Requested capacity", value="", placeholder="e.g. 50000", key=f"{prefix}_capacity")
    capacity_unit = right.selectbox("Unit", fee.CAPACITY_UNITS, key=f"{prefix}_capacity_unit")
    return capacity, capacity_unit


def fee_tab(table, catalog: points.Catalog) -> None:
    today = date.today()
    booked = choose_booking(catalog)
    if not booked:
        st.info("The tariff file has no points of this booking type.")
        return
    instrument, selection = choose_product(table, booked, today, "fee")
    capacity, capacity_unit = choose_capacity("fee")

    period = fee.resolve_period(instrument, **selection)
    if isinstance(period, fee.FeeError):
        st.warning(period.message)
        return
    product = f"{fee.INSTRUMENT_LABELS[instrument].lower()} {dates_text(*period)}"
    if isinstance(booked, Bundle):
        result = fee.calculate_bundle_fee(table, booked, instrument, period[0], period[1], capacity, capacity_unit)
        if isinstance(result, fee.FeeError):
            st.warning(result.message)
            return
        st.subheader(f"{booked.label()}: {product}")
        for side in result.sides:
            point = side.point
            st.markdown(f"#### {point.tso_name} {point.direction.lower()} {point.cleaned_name}")
            show_side(side, f"Monthly invoice ({point.tso_name})")
        show_bundle_total(result)
        return

    result = fee.calculate_fee(table, booked, instrument, period[0], period[1], capacity, capacity_unit)
    if isinstance(result, fee.FeeError):
        st.warning(result.message)
        return
    label = booked.lng_label() if booked.is_lng else f"{booked.tso_name} {booked.fee_label()}"
    st.subheader(f"{label}: {product}")
    show_side(result, "Monthly invoice")


# --- tab 3 -------------------------------------------------------------------------------------

GUARANTEE_ROWS = "guar_rows"  # the list of bookings, kept for the browser session
DASH = "–"
GUARANTEE_COLUMNS = ("Capacity fee", "GfON fee", "Capacity fee guarantee", "GfON fee guarantee", "Total guarantee")


def product_label(instrument: str, selection: dict) -> str:
    """The product as the guarantee table shows it, e.g. "Quarter 2026 Q4"."""
    if instrument == fee.GAS_YEAR:
        period = periods.gas_year_label(selection["gas_year"])
    elif instrument == fee.QUARTER:
        period = f"{selection['year']} Q{selection['quarter']}"
    elif instrument == fee.MONTH:
        period = f"{selection['year']}-{selection['month']:02d}"
    else:
        period = selection["day"].isoformat()
    return f"{fee.INSTRUMENT_LABELS[instrument]} {period}"


def number_text(value: Fraction) -> str:
    """An exact number with thousands commas: 100,000 or 1,234.5."""
    whole, _, decimals = money.format_exact(value).partition(".")
    return f"{int(whole):,}" + (f".{decimals}" if decimals else "")


def booking_guarantee(table, booking: dict):
    period = fee.resolve_period(booking["instrument"], **booking["selection"])
    if isinstance(period, fee.FeeError):
        return period
    return guarantee.calculate_guarantee(table, booking["point"], booking["instrument"], *period, booking["capacity"],
                                         booking["unit"], booking["stage"], booking["ceghix"],
                                         booking.get("surcharge"))


def surcharge_text(text) -> str:
    surcharge = guarantee.parse_surcharge(text)
    return DASH if isinstance(surcharge, fee.FeeError) or surcharge == 0 else number_text(surcharge)


def guarantee_record(booking: dict, result) -> dict:
    """One table row: the booking's inputs, then its amounts in EUR (blank when it cannot be priced)."""
    point = booking["point"]
    booked = booking["stage"] == guarantee.BOOKED
    record = {
        "TSO": point.tso_name,
        "Network point": f"{point.name} {point.flow}",
        "Product": product_label(booking["instrument"], booking["selection"]),
        "Capacity": f"{number_text(money.parse_number(booking['capacity']))} {booking['unit']}",
        "Stage": booking["stage"],
        "Surcharge (%)": surcharge_text(booking.get("surcharge")),
        "CEGHIX (EUR/MWh)": number_text(guarantee.parse_ceghix(booking["ceghix"])) if booked else DASH,
    }
    if isinstance(result, fee.FeeError):
        return record | dict.fromkeys(GUARANTEE_COLUMNS, "")
    amounts = (result.capacity_fee, result.gfon_fee, result.capacity_fee_guarantee, result.gfon_fee_guarantee,
               result.total_guarantee)
    return record | {column: DASH if amount is None else money.format_amount(amount, money.EUR)
                     for column, amount in zip(GUARANTEE_COLUMNS, amounts)}


def guarantee_total(results) -> dict:
    """The total row: the sum of each amount column over the priced rows, a dash counting as zero."""
    priced = [r for r in results if not isinstance(r, fee.FeeError)]
    sums = (
        sum(r.capacity_fee for r in priced),
        sum(r.gfon_fee or 0 for r in priced),
        sum(r.capacity_fee_guarantee for r in priced),
        sum(r.gfon_fee_guarantee or 0 for r in priced),
        sum(r.total_guarantee for r in priced),
    )
    return {"": "Total"} | {column: money.format_amount(amount, money.EUR) for column, amount in zip(GUARANTEE_COLUMNS, sums)}


def guarantee_tab(table, catalog: points.Catalog) -> None:
    today = date.today()
    tso = st.selectbox("TSO", list(guarantee.GUARANTEE_RULES), format_func=points.tso_name, key="guar_tso")
    if tso in guarantee.GUARANTEE_NOTES:
        with st.expander(f"How {points.tso_name(tso)} calculates the financial guarantee"):
            st.markdown(guarantee.GUARANTEE_NOTES[tso])
    tso_points = catalog.singles_of(tso)
    if not tso_points:
        st.info("The tariff file has no points of this TSO.")
        return
    point = st.selectbox("Network point", tso_points, format_func=lambda p: p.fee_label(catalog.capacity_type(p)),
                         key=f"guar_point_{tso}")
    instrument, selection = choose_product(table, point, today, "guar")
    capacity, capacity_unit = choose_capacity("guar")
    stage = st.radio("Stage", guarantee.STAGES, index=guarantee.STAGES.index(guarantee.BOOKED), horizontal=True,
                     key="guar_stage")
    surcharge = st.text_input("Auction surcharge (%)", value="", placeholder="e.g. 15", key="guar_surcharge")
    st.caption(guarantee.SURCHARGE_NOTE)
    ceghix = None
    if stage == guarantee.BOOKED:
        ceghix = st.text_input("CEGHIX (EUR/MWh)", value="", placeholder="e.g. 30.5", key="guar_ceghix")
        st.caption(guarantee.CEGHIX_NOTE)

    rows: list[dict] = st.session_state.setdefault(GUARANTEE_ROWS, [])
    if st.button("Add to list", key="guar_add"):
        booking = {"point": point, "instrument": instrument, "selection": selection, "capacity": capacity,
                   "unit": capacity_unit, "stage": stage, "ceghix": ceghix, "surcharge": surcharge}
        result = booking_guarantee(table, booking)
        if isinstance(result, fee.FeeError):
            st.warning(result.message)
        else:
            rows.append(booking)

    if not rows:
        st.info("Add a booking to start the list.")
        return
    results = [booking_guarantee(table, booking) for booking in rows]
    for booking, result in zip(rows, results):
        if isinstance(result, fee.FeeError):  # a row the current tariff file no longer prices
            st.warning(f"{booking['point'].name} {booking['point'].flow}, "
                       f"{product_label(booking['instrument'], booking['selection'])}: {result.message}")
    event = st.dataframe(pd.DataFrame([guarantee_record(b, r) for b, r in zip(rows, results)]), hide_index=True,
                         on_select="rerun", selection_mode="multi-row", key="guar_table")
    st.dataframe(pd.DataFrame([guarantee_total(results)]), hide_index=True)
    st.caption("Amounts in EUR.")

    left, right = st.columns(2)
    if left.button("Remove selected rows", key="guar_remove", disabled=not event.selection.rows):
        selected = set(event.selection.rows)
        st.session_state[GUARANTEE_ROWS] = [b for i, b in enumerate(rows) if i not in selected]
        st.rerun()
    if right.button("Clear list", key="guar_clear"):
        st.session_state[GUARANTEE_ROWS] = []
        st.rerun()


# --- page ----------------------------------------------------------------------------------------

st.title("Route Tariff and Capacity Fee Calculator")
load_result, source_label = load_data()
st.sidebar.caption(source_label)

if not load_result.ok:
    for message in load_result.errors:
        st.error(message)
    st.stop()

if load_result.warnings:
    with st.sidebar.expander(f"{len(load_result.warnings)} tariff row(s) excluded"):
        for message in load_result.warnings:
            st.write(message)

catalog = points.build_catalog(load_result.table)
if catalog.unnamed:
    with st.sidebar.expander(f"{len(catalog.unnamed)} point(s) left out: no border flow in the name"):
        for name in catalog.unnamed:
            st.write(name)
route, capacity_fee, bank_guarantee = st.tabs(
    ["Route Tariff Calculator", "Capacity Fee Calculator", "Bank Guarantee Calculator"])
with route:
    route_tab(load_result.table, points.build_network(catalog))
with capacity_fee:
    fee_tab(load_result.table, catalog)
with bank_guarantee:
    guarantee_tab(load_result.table, catalog)
