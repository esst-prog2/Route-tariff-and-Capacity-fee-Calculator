"""Builders for small hand-made tariff tables, so tests never depend on the
prices in the sample file."""

from __future__ import annotations

import pandas as pd

from core import periods
from core.tariffs import TariffTable, parse_frame

WD_COLUMNS = [f"WD_{c.split('_')[1]}" for c in periods.MONTH_COLUMNS]


def make_row(
    eic="21Z000000000003C",
    direction="Entry",
    valid_from="2025-10-01",
    valid_to="2026-09-30",
    name="Test point",
    operator="FGSZ",
    capacity="Firm",
    currency="HUF",
    unit="kWh/h",
    prices=None,
):
    """One source row; every price defaults to a round number, override via `prices`."""
    row = {
        "EIC": eic,
        "Network point": name,
        "System operator": operator,
        "Direction": direction,
        "Currency": currency,
        "Measure unit": unit,
        "Capacity_type": capacity,
        "Valid from": pd.Timestamp(valid_from),
        "Valid to": pd.Timestamp(valid_to) if valid_to else pd.NaT,
    }
    row["Year"] = 1000.0
    for column in periods.QUARTER_COLUMNS:
        row[column] = 300.0
    for column in periods.MONTH_COLUMNS:
        row[column] = 100.0
    for column in periods.DAY_COLUMNS:
        row[column] = 4.0
    for column in WD_COLUMNS:
        row[column] = 0.5
    row.update(prices or {})
    return row


def make_frame(*rows) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


def make_table(*rows) -> TariffTable:
    result = parse_frame(make_frame(*rows))
    assert result.ok, result.errors
    return result.table
