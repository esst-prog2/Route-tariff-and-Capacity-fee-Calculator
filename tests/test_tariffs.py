from datetime import date
from fractions import Fraction

import pandas as pd

from core import tariffs
from core.tariffs import load_tariffs, parse_frame, resolve_tariff_path

from .helpers import make_frame, make_row, make_table

EIC = "21Z000000000003C"


# --- 3.1 file-level validation ------------------------------------------------

def test_missing_column_is_reported_by_name_not_raised():
    frame = make_frame(make_row()).drop(columns=["Q1_Jan"])
    result = parse_frame(frame)
    assert not result.ok
    assert "Q1_Jan" in result.errors[0]


def test_unreadable_files_give_a_message(tmp_path):
    not_excel = tmp_path / "notes.txt"
    not_excel.write_text("hello")
    assert not load_tariffs(not_excel).ok
    assert "could not be read" in load_tariffs(not_excel).errors[0]
    assert not load_tariffs(tmp_path / "missing.xlsx").ok


def test_file_without_fgsz_firm_rows_is_rejected():
    result = parse_frame(make_frame(make_row(operator="BGTRGAZ")))
    assert not result.ok and "no FGSZ Firm" in result.errors[0]


def test_reads_an_excel_file_and_the_capacity_fee_sheet(tmp_path):
    path = tmp_path / "t.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"x": [1]}).to_excel(writer, sheet_name="Other", index=False)
        make_frame(make_row(), make_row(eic="21Z000000000139O")).to_excel(
            writer, sheet_name="Capacity_fee", index=False
        )
    result = load_tariffs(path)
    assert result.ok and len(result.table) == 2


# --- 3.2 row-level validation --------------------------------------------------

def test_row_with_blank_price_is_excluded_and_named():
    good = make_row(eic=EIC)
    bad = make_row(eic="21Z000000000139O", name="Bad point", prices={"D_Dec": None})
    result = parse_frame(make_frame(good, bad))
    assert result.ok and len(result.table) == 1
    assert len(result.warnings) == 1
    assert "Row 3" in result.warnings[0] and "Bad point" in result.warnings[0]
    assert "D_Dec" in result.warnings[0]
    assert result.table.find_row("21Z000000000139O", "Entry", date(2026, 1, 1)) is None


def test_bad_dates_currency_and_unit_exclude_the_row():
    good = make_row()
    rows = [
        make_row(eic="A", valid_from="2025-10-01", valid_to="2025-01-01"),
        make_row(eic="B", currency="EUR"),
        make_row(eic="C", unit="kWh/d"),
    ]
    frame = make_frame(good, *rows)
    frame.loc[3, "Valid from"] = pd.NaT  # row C: wrong unit and no start date
    result = parse_frame(frame)
    assert len(result.table) == 1
    assert len(result.warnings) == 3
    assert any("before" in w for w in result.warnings)
    assert any("currency" in w for w in result.warnings)
    assert any("unit" in w and "'Valid from'" in w for w in result.warnings)


# --- 3.3 scope filter and reshape ---------------------------------------------

def test_only_fgsz_firm_entry_exit_rows_are_kept():
    table = make_table(
        make_row(eic="E1", direction="Entry"),
        make_row(eic="X1", direction="Exit"),
        make_row(eic="I1", capacity="Interruptible"),
        make_row(eic="O1", operator="GCA"),
        make_row(eic="D1", direction="DSO_Exit"),
        make_row(eic="S1", direction="Storage"),
    )
    assert sorted(table.keys()) == [("E1", "Entry"), ("X1", "Exit")]


def test_within_day_columns_never_reach_the_price_map():
    row = make_table(make_row()).find_row(EIC, "Entry", date(2026, 1, 1))
    assert not any(column.startswith("WD_") for column in row.prices)
    assert len(row.prices) == 29  # Year + 4 quarters + 12 months + 12 days


def test_month_mapping_uses_the_hungarian_may_column():
    row = make_table(make_row(prices={"M_Maj": 555.5, "D_Maj": 7.25, "Q2_Apr": 900.0})).find_row(
        EIC, "Entry", date(2026, 5, 1)
    )
    assert row.month_price(5) == Fraction("555.5")
    assert row.day_price(5) == Fraction("7.25")
    assert row.quarter_price(2) == 900
    assert row.year_price() == 1000


# --- 3.4 lookup by date ------------------------------------------------------------

def test_row_spanning_several_gas_years():
    table = make_table(make_row(valid_from="2021-10-01", valid_to="2025-09-30"))
    assert table.find_row(EIC, "Entry", date(2024, 3, 15)) is not None
    assert table.find_row(EIC, "Entry", date(2025, 9, 30)) is not None
    assert table.find_row(EIC, "Entry", date(2025, 10, 1)) is None


def test_open_ended_row_applies_to_later_dates():
    table = make_table(make_row(valid_from="2026-10-01", valid_to=None))
    row = table.find_row(EIC, "Entry", date(2029, 5, 10))
    assert row is not None and row.open_ended
    assert table.find_row(EIC, "Entry", date(2026, 9, 30)) is None


def test_date_before_earliest_row_has_no_tariff():
    table = make_table(make_row(valid_from="2025-10-01"))
    assert table.find_row(EIC, "Entry", date(2024, 1, 1)) is None
    assert table.earliest_valid_from(EIC, "Entry") == date(2025, 10, 1)
    assert table.earliest_valid_from("nope", "Entry") is None


def test_direction_is_part_of_the_key():
    table = make_table(make_row(direction="Entry", prices={"Year": 1.0}), make_row(direction="Exit", prices={"Year": 2.0}))
    assert table.find_row(EIC, "Entry", date(2026, 1, 1)).year_price() == 1
    assert table.find_row(EIC, "Exit", date(2026, 1, 1)).year_price() == 2


def test_later_row_supersedes_an_open_ended_one():
    table = make_table(
        make_row(valid_from="2026-10-01", valid_to=None, prices={"Year": 1.0}),
        make_row(valid_from="2027-10-01", valid_to=None, prices={"Year": 2.0}),
    )
    assert table.find_row(EIC, "Entry", date(2027, 6, 1)).year_price() == 1
    assert table.find_row(EIC, "Entry", date(2028, 1, 1)).year_price() == 2


# --- 3.5 source report ------------------------------------------------------------

def test_source_text():
    open_row = make_table(make_row(valid_from="2026-10-01", valid_to=None)).find_row(EIC, "Entry", date(2027, 1, 1))
    closed_row = make_table(make_row()).find_row(EIC, "Entry", date(2026, 1, 1))
    assert open_row.source_text() == "from 2026-10-01 (open-ended)"
    assert closed_row.source_text() == "from 2025-10-01"


# --- 3.6 configured path -------------------------------------------------------------

def test_default_path_is_the_committed_sample_and_loads():
    path = resolve_tariff_path({})
    assert path == tariffs.DEFAULT_SAMPLE_PATH and path.exists()
    result = load_tariffs(path)
    assert result.ok and len(result.table) > 0


def test_environment_variable_points_at_another_file(tmp_path):
    other = tmp_path / "other.xlsx"
    make_frame(make_row(eic="ONLYHERE")).to_excel(other, sheet_name="Capacity_fee", index=False)
    path = resolve_tariff_path({tariffs.PATH_ENV_VAR: str(other)})
    assert path == other
    assert load_tariffs(path).table.keys() == [("ONLYHERE", "Entry")]
    assert resolve_tariff_path({tariffs.PATH_ENV_VAR: "  "}) == tariffs.DEFAULT_SAMPLE_PATH


# --- uploaded files arrive as bytes (what the UI uploader passes) ---------------------------------

def _xlsx_bytes(frame) -> bytes:
    import io

    buffer = io.BytesIO()
    frame.to_excel(buffer, sheet_name="Capacity_fee", index=False)
    return buffer.getvalue()


def test_uploaded_bytes_load_like_a_path():
    import io

    result = load_tariffs(io.BytesIO(_xlsx_bytes(make_frame(make_row()))))
    assert result.ok and len(result.table) == 1


def test_uploaded_file_without_q1_jan_gives_a_plain_message():
    import io

    result = load_tariffs(io.BytesIO(_xlsx_bytes(make_frame(make_row()).drop(columns=["Q1_Jan"]))))
    assert not result.ok
    assert result.errors == ["The tariff file is missing required column(s): Q1_Jan."]


def test_uploaded_garbage_bytes_give_a_message_not_an_exception():
    import io

    result = load_tariffs(io.BytesIO(b"this is not an excel file"))
    assert not result.ok and "could not be read" in result.errors[0]
