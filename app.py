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
from core.tariffs import LoadResult, load_tariffs, resolve_tariff_path

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

def dec4(value: Fraction) -> str:
    return money.format_decimal(value, 4)


def plain_rate(rate: Fraction) -> str:
    text = money.format_decimal(rate, 4)
    return text.rstrip("0").rstrip(".") if "." in text else text


def dates_text(start: date, end: date) -> str:
    return start.isoformat() if start == end else f"{start.isoformat()} to {end.isoformat()}"


# --- tab 1 -----------------------------------------------------------------------------------

def route_tab(table) -> None:
    st.selectbox("TSO", points.TSOS, key="route_tso")
    entries, exits = points.entries(), points.exits()
    default_exit = next((i for i, p in enumerate(exits) if p.name == "Kiskundorozsma"), 0)

    left, right = st.columns(2)
    entry = left.selectbox("Entry point", entries, format_func=lambda p: p.route_label(), key="route_entry")
    exit_ = right.selectbox("Exit point", exits, index=default_exit, format_func=lambda p: p.route_label(), key="route_exit")

    left, right = st.columns(2)
    start = left.date_input("Booking start (inclusive)", value=date(2026, 10, 1), min_value=date(2000, 1, 1),
                            max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="route_start")
    end = right.date_input("Booking end (inclusive)", value=date(2027, 3, 31), min_value=date(2000, 1, 1),
                           max_value=date(2100, 12, 31), format="YYYY-MM-DD", key="route_end")

    fx_text = st.text_input("FX rate (HUF per 1 EUR)", value="", placeholder="e.g. 400", key="route_fx",
                            help="Type today's rate. EUR/MWh is shown once a rate is entered.")

    result = calculate_route(table, entry, exit_, start, end, fx_text)
    if isinstance(result, RouteError):
        st.error(result.message)
        return

    plan = result.plan
    st.subheader(f"{entry.cleaned_name} to {exit_.cleaned_name}")
    st.caption(f"Booking period {dates_text(plan.start, plan.end)} ({plan.days} days). "
               "Prices are entry + exit, in HUF per 1 kWh/h for the product period.")

    st.dataframe(
        pd.DataFrame(
            {
                "Segment": [dates_text(s.start, s.end) for s in plan.segments],
                "Product": [s.product for s in plan.segments],
                "HUF per kWh/h": [dec4(s.price) for s in plan.segments],
                "Tariff used": [s.tariff_used for s in plan.segments],
            }
        ),
        hide_index=True, width="stretch",
    )

    has_rate = result.fx_rate is not None
    rows = {
        "Cheapest combination": (plan.total, result.huf_per_mwh, result.eur_per_mwh),
        "All daily": (plan.all_daily_total, result.all_daily_huf_per_mwh, result.all_daily_eur_per_mwh),
        "Saving": (
            plan.saving,
            result.all_daily_huf_per_mwh - result.huf_per_mwh,
            None if not has_rate else result.all_daily_eur_per_mwh - result.eur_per_mwh,
        ),
    }
    summary = {"": list(rows), "HUF per kWh/h": [dec4(v[0]) for v in rows.values()],
               "HUF/MWh": [dec4(v[1]) for v in rows.values()]}
    if has_rate:
        summary["EUR/MWh"] = [dec4(v[2]) for v in rows.values()]
    st.dataframe(pd.DataFrame(summary), hide_index=True, width="stretch")

    if has_rate:
        st.caption(f"EUR/MWh at 1 EUR = {plain_rate(result.fx_rate)} HUF. "
                   "HUF/MWh assumes the booked capacity is used fully (24 h x days).")
    elif result.fx_message:
        st.warning(result.fx_message)
    else:
        st.info("Enter today's HUF per EUR rate to see EUR/MWh.")


# --- tab 2 -----------------------------------------------------------------------------------

def fee_tab(table) -> None:
    today = date.today()
    st.selectbox("TSO", points.TSOS, key="fee_tso")
    default_point = next((i for i, p in enumerate(points.POINTS) if p.name == "Kiskundorozsma 2"), 0)
    point = st.selectbox("Network point", points.POINTS, index=default_point,
                         format_func=lambda p: p.fee_label(), key="fee_point")
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

    st.subheader(f"{point.fee_label()}: {fee.INSTRUMENT_LABELS[instrument].lower()} {dates_text(result.start, result.end)}")
    left, middle, right = st.columns(3)
    left.metric("Capacity (kWh/h)", money.format_decimal(result.capacity_kwh_h, 2))
    middle.metric(f"Price ({result.price_column}, HUF per kWh/h)", dec4(result.price))
    right.metric("Total cost (HUF)", money.format_whole(result.total))
    st.caption(f"Tariff used: {result.tariff_used}. All amounts are in HUF; the total is rounded to whole forints.")

    lines = [(f"{line.year}-{line.month:02d}", line.days, money.format_whole(line.amount)) for line in result.invoice]
    lines.append(("Total", sum(line.days for line in result.invoice), money.format_whole(result.total)))
    st.markdown("**Monthly invoice**")
    st.dataframe(pd.DataFrame(lines, columns=["Month", "Days", "Amount (HUF)"]), hide_index=True, width="stretch")


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
