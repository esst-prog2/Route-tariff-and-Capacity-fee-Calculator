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


KIREEVO = "Kireevo/Zaychar (BG - RS)"
KISKUNDOROZSMA_2 = "Kiskundorozsma 2 (HU - RS)"
_CORRIDOR = ["BG", KIREEVO, "RS", KISKUNDOROZSMA_2, "HU"]


def corridor(begin: str, end: str) -> tuple[str, list[str]]:
    """The old HU - RS - BG corridor route from `begin` to `end` as (beginning, map point labels)."""
    order = _CORRIDOR if _CORRIDOR.index(begin) < _CORRIDOR.index(end) else _CORRIDOR[::-1]
    i, j = order.index(begin), order.index(end)
    return begin, order[i + 1:j:2]


def corridor_points(begin: str, end: str):
    """The exit and entry Points of the old corridor route, in route order (for building tables)."""
    from core import points

    order = ["HU", "RS", "BG"]
    i, j = order.index(begin), order.index(end)
    step = 1 if j > i else -1
    path = [order[k] for k in range(i, j + step, step)]
    eics = {frozenset({"HU", "RS"}): "21Z000000000505P", frozenset({"RS", "BG"}): "58Z-000000007-KZ"}
    tsos = {"HU": points.FGSZ, "RS": points.GASTRANS, "BG": points.BULGARTRANSGAZ}
    found = []
    for a, b in zip(path, path[1:]):
        eic, flow = eics[frozenset({a, b})], f"{a}>{b}"
        for tso, direction in ((tsos[a], points.EXIT), (tsos[b], points.ENTRY)):
            found.append(next(p for p in points.POINTS if p.key == (tso, eic, direction) and p.flow == flow))
    return found
