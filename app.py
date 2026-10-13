"""Streamlit front end. All business rules live in `core/`; this file only
collects inputs and formats results."""

from __future__ import annotations

import os
from datetime import date
from fractions import Fraction

import pandas as pd
import streamlit as st

from core import fee, money, periods, points
from core.route import RouteError, calculate_route
from core.tariffs import INTERRUPTIBLE, LoadResult, load_tariffs, resolve_tariff_path

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


def dates_text(start: date, end: date) -> str:
    return start.isoformat() if start == end else f"{start.isoformat()} to {end.isoformat()}"


# --- tab 1 -----------------------------------------------------------------------------------

def route_tab(table) -> None:
    left, right = st.columns(2)
    begin = left.selectbox("Route beginning", points.COUNTRIES, index=points.COUNTRIES.index("BG"), key="route_begin")
    end_country = right.selectbox("Route ending", points.COUNTRIES, index=points.COUNTRIES.index("HU"), key="route_end_country")

    left, right = st.columns(2)
    start = left.date_input("Booking start (inclusive)", value=date(2026, 10, 1), min_value=date(2000, 1, 1),
                            max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="route_start")
    end = right.date_input("Booking end (inclusive)", value=date(2027, 3, 31), min_value=date(2000, 1, 1),
                           max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="route_end")

    fx_text = ""
    if begin != end_country and "HU" in (begin, end_country):
        fx_text = st.text_input("FX rate (HUF per 1 EUR)", value="", placeholder="e.g. 400", key="route_fx",
                                help="Type today's rate. FGSZ's and the route's EUR/MWh are shown once a rate is entered.")

    result = calculate_route(table, begin, end_country, start, end, fx_text)
    if isinstance(result, RouteError):
        st.error(result.message)
        return

    st.subheader(f"{begin} to {end_country}")
    st.caption(f"Booking period {dates_text(start, end)} ({result.days} days), hub to hub.")

    st.markdown("**Network points on the route**")
    capacity_types = [table.capacity_type(*p.key) for p in result.points]
    st.dataframe(
        pd.DataFrame(
            {
                "#": list(range(1, len(result.points) + 1)),
                "TSO": [p.tso_name for p in result.points],
                "Point": [p.cleaned_name for p in result.points],
                "EIC": [p.eic for p in result.points],
                "Direction": [p.direction for p in result.points],
                "Capacity type": capacity_types,
            }
        ),
        hide_index=True, width="stretch",
    )
    if INTERRUPTIBLE in capacity_types:
        st.warning("Interruptible capacity is used where a point has no Firm tariff; "
                   "the TSO can interrupt it.")

    for leg in result.legs:
        unit_text = f"{leg.currency} per {leg.unit}"
        names = ", ".join(f"{p.direction.lower()} {p.cleaned_name}" for p in leg.points)
        st.markdown(f"**{leg.tso_name}**: {names}. Prices in {unit_text} for the product period.")
        st.dataframe(
            pd.DataFrame(
                {
                    "Segment": [dates_text(s.start, s.end) for s in leg.plan.segments],
                    "Product": [s.product for s in leg.plan.segments],
                    unit_text: [dec4(s.price) for s in leg.plan.segments],
                    "Days outside period": [s.days_outside(leg.plan.start, leg.plan.end) for s in leg.plan.segments],
                    "Tariff used": [s.tariff_used for s in leg.plan.segments],
                }
            ),
            hide_index=True, width="stretch",
        )

    over_booked = [f"{leg.tso_name} {leg.plan.days_outside} day(s)" for leg in result.legs if leg.plan.days_outside]
    if over_booked:
        st.info(f"Over-booking: {', '.join(over_booked)} outside the booking period, because a longer product "
                "costs less than covering only the booked days. Per-MWh figures use the booked days only.")

    st.markdown("**Summary per TSO**")
    st.dataframe(
        pd.DataFrame(
            {
                "TSO": [leg.tso_name for leg in result.legs],
                "Unit": [f"{leg.currency} per {leg.unit}" for leg in result.legs],
                "Cheapest": [dec4(leg.plan.total) for leg in result.legs],
                "All daily": [dec4(leg.plan.all_daily_total) for leg in result.legs],
                "Saving": [dec4(leg.plan.saving) for leg in result.legs],
                "Per MWh": [f"{dec4(leg.per_mwh)} {leg.currency}/MWh" for leg in result.legs],
                "EUR/MWh": [dec4(leg.eur_per_mwh) for leg in result.legs],
            }
        ),
        hide_index=True, width="stretch",
    )

    if result.eur_per_mwh is not None:
        st.markdown("**Route total (EUR/MWh)**")
        st.dataframe(
            pd.DataFrame(
                {
                    "": ["Cheapest combination", "All daily", "Saving"],
                    "EUR/MWh": [dec4(result.eur_per_mwh), dec4(result.all_daily_eur_per_mwh),
                                dec4(result.saving_eur_per_mwh)],
                }
            ),
            hide_index=True, width="stretch",
        )
        note = "Per-MWh figures assume the booked capacity is used fully on the booked days."
        if result.fx_rate is not None:
            note = f"FGSZ's EUR/MWh at 1 EUR = {plain_rate(result.fx_rate)} HUF. " + note
        st.caption(note)
    elif result.fx_message:
        st.warning(result.fx_message)
    else:
        st.info("Enter today's HUF per EUR rate to see FGSZ's and the route's EUR/MWh.")


# --- tab 2 -----------------------------------------------------------------------------------

def fee_tab(table) -> None:
    today = date.today()
    tso = st.selectbox("TSO", points.TSOS, format_func=points.tso_name, key="fee_tso")
    tso_points = points.points_of(tso)
    default_point = next((i for i, p in enumerate(tso_points) if p.name == "Kiskundorozsma 2"), 0)
    point = st.selectbox("Network point", tso_points, index=default_point,
                         format_func=lambda p: p.fee_label(table.capacity_type(*p.key)), key=f"fee_point_{tso}")
    instrument = st.selectbox("Product instrument", fee.INSTRUMENTS, index=fee.INSTRUMENTS.index(fee.QUARTER),
                              format_func=fee.INSTRUMENT_LABELS.get, key="fee_instrument")

    gas_years = fee.gas_year_choices(table, point, today)
    calendar_years = fee.calendar_year_choices(table, point, today)
    year_default = calendar_years.index(2026) if 2026 in calendar_years else 0

    selection: dict = {}
    if instrument == fee.GAS_YEAR:
        current = periods.gas_year_start_year(today)
        selection["gas_year"] = st.selectbox(
            "Gas year", gas_years, index=gas_years.index(current) if current in gas_years else 0,
            format_func=periods.gas_year_label, key="fee_gas_year")
    elif instrument == fee.QUARTER:
        left, right = st.columns(2)
        selection["year"] = left.selectbox("Year", calendar_years, index=year_default, key="fee_q_year")
        selection["quarter"] = right.selectbox("Quarter", [1, 2, 3, 4], index=3,
                                               format_func=lambda q: f"Q{q} ({QUARTER_MONTHS[q]})", key="fee_quarter")
    elif instrument == fee.MONTH:
        left, right = st.columns(2)
        selection["year"] = left.selectbox("Year", calendar_years, index=year_default, key="fee_m_year")
        selection["month"] = right.selectbox("Month", list(range(1, 13)), format_func=lambda m: f"{m:02d}", key="fee_month")
    else:
        selection["day"] = st.date_input("Day", value=date(2026, 12, 5), min_value=date(2000, 1, 1),
                                         max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="fee_day")

    capacity = st.text_input("Requested capacity (kWh/d)", value="", placeholder="e.g. 50000", key="fee_capacity")

    period = fee.resolve_period(instrument, **selection)
    if isinstance(period, fee.FeeError):
        st.warning(period.message)
        return
    result = fee.calculate_fee(table, point, instrument, period[0], period[1], capacity)
    if isinstance(result, fee.FeeError):
        st.warning(result.message)
        return

    currency = result.currency
    st.subheader(f"{point.tso_name} {point.fee_label()}: "
                 f"{fee.INSTRUMENT_LABELS[instrument].lower()} {dates_text(result.start, result.end)}")
    left, middle, right = st.columns(3)
    left.metric(f"Capacity ({result.unit})", money.format_decimal(result.capacity, 2))
    middle.metric(f"Price ({result.price_column}, {currency} per {result.unit})", dec4(result.price))
    right.metric(f"Total cost ({currency})", money.format_amount(result.total, currency))
    rounding = "whole forints" if money.CURRENCY_DECIMALS[currency] == 0 else "cents"
    st.caption(f"Tariff used: {result.tariff_used}. All amounts are in {currency}; the total is rounded to {rounding}.")
    if result.capacity_type == INTERRUPTIBLE:
        st.warning("This point has no Firm tariff, so Interruptible capacity is priced; the TSO can interrupt it.")

    lines = [(f"{line.year}-{line.month:02d}", line.days, money.format_amount(line.amount, currency))
             for line in result.invoice]
    lines.append(("Total", sum(line.days for line in result.invoice), money.format_amount(result.total, currency)))
    st.markdown("**Monthly invoice**")
    st.dataframe(pd.DataFrame(lines, columns=["Month", "Days", f"Amount ({currency})"]), hide_index=True, width="stretch")


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

route, capacity_fee = st.tabs(["Route Tariff Calculator", "Capacity Fee Calculator"])
with route:
    route_tab(load_result.table)
with capacity_fee:
    fee_tab(load_result.table)
