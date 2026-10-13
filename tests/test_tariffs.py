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


def test_file_without_supported_tso_rows_is_rejected():
    result = parse_frame(make_frame(make_row(operator="EDDGAZ")))
    assert not result.ok and "no Entry/Exit rows of a supported TSO" in result.errors[0]


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
    assert result.table.find_row("FGSZ", "21Z000000000139O", "Entry", date(2026, 1, 1)) is None


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

def test_only_the_supported_tsos_entry_exit_rows_are_kept():
    table = make_table(
        make_row(eic="E1", direction="Entry"),
        make_row(eic="X1", direction="Exit"),
        make_row(eic="G1", operator="Gastran", currency="EUR"),
        make_row(eic="B1", operator="BGTRGAZ", currency="EUR", unit="kWh/d"),
        make_row(eic="O1", operator="GCA", currency="EUR"),
        make_row(eic="N1", operator="EDDGAZ"),
        make_row(eic="D1", direction="DSO_Exit"),
        make_row(eic="S1", direction="Storage"),
    )
    assert sorted(table.keys()) == [
        ("BGTRGAZ", "B1", "Entry"), ("FGSZ", "E1", "Entry"), ("FGSZ", "X1", "Exit"), ("GCA", "O1", "Entry"),
        ("Gastran", "G1", "Entry"),
    ]


def test_twenty_one_tsos_are_in_scope():
    assert len(tariffs.TSOS) == 21
    assert tariffs.TSO_NAMES["EUSTR"] == "Eustream" and tariffs.TSO_NAMES["GCA"] == "Gas Connect Austria"
    assert tariffs.TSO_FORMATS["TRANSGA"] == ("RON", "kWh/h") and tariffs.TSO_FORMATS["plinacr"] == ("EUR", "kWh/d")


def test_excluded_operators_ignored_on_the_real_file():
    result = load_tariffs(tariffs.DEFAULT_PATH)
    excluded = {"EDDGAZ", "EgDegel", "HEXUM", "ISDP", "LNGCRO", "MFGT", "NKM_el", "TIGAZ"}
    assert result.ok
    assert {tso for tso, _, _ in result.table.keys()} == set(tariffs.TSOS)
    assert not [w for w in result.warnings if any(code in w for code in excluded)]


def test_other_capacity_types_ignored():
    brandov = "21Z0000000004863"
    result = parse_frame(make_frame(
        make_row(eic=brandov, operator="GASCADE", currency="EUR", capacity="DZK", prices={"Year": 9.0}),
        make_row(eic=brandov, operator="GASCADE", currency="EUR", capacity="Firm", prices={"Year": 1.0}),
    ))
    assert result.ok and len(result.table) == 1 and result.warnings == []
    assert result.table.find_row("GASCADE", brandov, "Entry", date(2026, 1, 1)).year_price() == 1


def test_dzk_only_point_is_not_used():
    result = parse_frame(make_frame(
        make_row(eic="F"), make_row(eic="Z", operator="GASCADE", currency="EUR", capacity="DZK"),
    ))
    assert result.table.keys() == [("FGSZ", "F", "Entry")] and result.warnings == []


def test_interruptible_rows_ignored():
    table = make_table(
        make_row(prices={"Year": 1.0}),
        make_row(capacity="Interruptible", prices={"Year": 2.0}),
    )
    assert len(table) == 1
    assert table.find_row("FGSZ", EIC, "Entry", date(2026, 1, 1)).year_price() == 1
    assert table.capacity_type("FGSZ", EIC, "Entry") == "Firm"


def test_interruptible_used_where_firm_is_missing():
    kireevo = "58Z-000000007-KZ"
    table = make_table(
        make_row(eic=kireevo, direction="Exit", operator="Gastran", currency="EUR", capacity="Interruptible",
                 valid_from="2025-10-01", valid_to="2026-09-30", prices={"Year": 8.55}),
        make_row(eic=kireevo, direction="Exit", operator="Gastran", currency="EUR", capacity="Interruptible",
                 valid_from="2026-10-01", valid_to=None, prices={"Year": 5.9}),
        make_row(eic=kireevo, direction="Entry", operator="Gastran", currency="EUR"),
    )
    assert table.capacity_type("Gastran", kireevo, "Exit") == "Interruptible"
    assert table.capacity_type("Gastran", kireevo, "Entry") == "Firm"
    assert table.find_row("Gastran", kireevo, "Exit", date(2027, 1, 1)).year_price() == Fraction("5.9")


def test_firm_and_interruptible_rows_of_one_point_are_never_mixed():
    # Firm only from 2026-10-01: earlier dates have no tariff rather than an Interruptible one.
    table = make_table(
        make_row(capacity="Interruptible", valid_from="2025-10-01", valid_to="2026-09-30"),
        make_row(capacity="Firm", valid_from="2026-10-01", valid_to=None),
    )
    assert table.find_row("FGSZ", EIC, "Entry", date(2026, 1, 1)) is None
    assert table.find_row("FGSZ", EIC, "Entry", date(2026, 10, 1)).capacity_type == "Firm"


# --- per-TSO currency and unit ------------------------------------------------------------

def test_each_tso_keeps_its_own_currency_and_unit():
    table = make_table(
        make_row(eic="F"), make_row(eic="G", operator="Gastran", currency="EUR"),
        make_row(eic="B", operator="BGTRGAZ", currency="EUR", unit="kWh/d"),
    )
    day = date(2026, 1, 1)
    assert (table.find_row("FGSZ", "F", "Entry", day).currency, table.find_row("FGSZ", "F", "Entry", day).unit) == ("HUF", "kWh/h")
    assert (table.find_row("Gastran", "G", "Entry", day).currency, table.find_row("Gastran", "G", "Entry", day).unit) == ("EUR", "kWh/h")
    assert (table.find_row("BGTRGAZ", "B", "Entry", day).currency, table.find_row("BGTRGAZ", "B", "Entry", day).unit) == ("EUR", "kWh/d")


def test_bulgartransgaz_bgn_rows_skipped_silently():
    bgn = make_row(eic="B", operator="BGTRGAZ", currency="BGN", unit="kWh/d", valid_from="2025-10-01", valid_to="2025-12-31")
    eur = make_row(eic="B", operator="BGTRGAZ", currency="EUR", unit="kWh/d", valid_from="2026-01-01", valid_to=None)
    result = parse_frame(make_frame(bgn, eur))
    assert result.ok and len(result.table) == 1 and result.warnings == []
    assert result.table.find_row("BGTRGAZ", "B", "Entry", date(2025, 12, 1)) is None
    assert result.table.earliest_valid_from("BGTRGAZ", "B", "Entry") == date(2026, 1, 1)


def test_plinacro_hrk_rows_skipped_silently():
    hrk_h = make_row(eic="P", operator="plinacr", currency="HRK", unit="kWh/h", valid_from="2022-01-01", valid_to="2022-12-31")
    hrk_d = make_row(eic="P", operator="plinacr", currency="HRK", unit="kWh/d", valid_from="2024-01-01", valid_to="2024-12-31")
    eur = make_row(eic="P", operator="plinacr", currency="EUR", unit="kWh/d", valid_from="2025-01-01", valid_to=None)
    result = parse_frame(make_frame(hrk_h, hrk_d, eur))
    assert result.ok and len(result.table) == 1 and result.warnings == []
    assert result.table.earliest_valid_from("plinacr", "P", "Entry") == date(2025, 1, 1)


def test_unsupported_currency_and_unexpected_unit_are_reported():
    result = parse_frame(make_frame(
        make_row(eic="OK"),
        make_row(eic="F", name="FGSZ in EUR", currency="EUR"),
        make_row(eic="G", name="Gastrans in kWh/d", operator="Gastran", currency="EUR", unit="kWh/d"),
    ))
    assert result.ok and len(result.table) == 1 and len(result.warnings) == 2
    assert "FGSZ in EUR" in result.warnings[0] and "currency is EUR" in result.warnings[0]
    assert "Gastrans in kWh/d" in result.warnings[1] and "unit is kWh/d" in result.warnings[1]


def test_other_currency_cell_per_kwh_h():
    table = make_table(make_row(eic="T", operator="TRANSGA", currency="RON", prices={"Q4_Oct": 11.892288}))
    row = table.find_row("TRANSGA", "T", "Entry", date(2025, 10, 1))
    assert (row.currency, row.unit) == ("RON", "kWh/h")
    assert 2000 * row.quarter_price(4) == Fraction("23784.576")


def test_bulgartransgaz_cell_is_per_kwh_d_for_the_whole_period():
    row = make_table(make_row(eic="B", operator="BGTRGAZ", currency="EUR", unit="kWh/d",
                              prices={"Year": 0.981251})).find_row("BGTRGAZ", "B", "Entry", date(2026, 1, 1))
    assert 50_000 * row.year_price() == Fraction("49062.55")


def test_same_eic_and_direction_at_two_tsos():
    kireevo = "58Z-000000007-KZ"
    table = make_table(
        make_row(eic=kireevo, operator="Gastran", currency="EUR", prices={"Year": 12.4}),
        make_row(eic=kireevo, operator="BGTRGAZ", currency="EUR", unit="kWh/d", prices={"Year": 0.488242}),
    )
    day = date(2026, 1, 1)
    assert table.find_row("Gastran", kireevo, "Entry", day).year_price() == Fraction("12.4")
    assert table.find_row("BGTRGAZ", kireevo, "Entry", day).year_price() == Fraction("0.488242")


def test_within_day_columns_never_reach_the_price_map():
    row = make_table(make_row()).find_row("FGSZ", EIC, "Entry", date(2026, 1, 1))
    assert not any(column.startswith("WD_") for column in row.prices)
    assert len(row.prices) == 29  # Year + 4 quarters + 12 months + 12 days


def test_month_mapping_uses_the_hungarian_may_column():
    row = make_table(make_row(prices={"M_Maj": 555.5, "D_Maj": 7.25, "Q2_Apr": 900.0})).find_row(
        "FGSZ", EIC, "Entry", date(2026, 5, 1)
    )
    assert row.month_price(5) == Fraction("555.5")
    assert row.day_price(5) == Fraction("7.25")
    assert row.quarter_price(2) == 900
    assert row.year_price() == 1000


# --- 3.4 lookup by date ------------------------------------------------------------

def test_row_spanning_several_gas_years():
    table = make_table(make_row(valid_from="2021-10-01", valid_to="2025-09-30"))
    assert table.find_row("FGSZ", EIC, "Entry", date(2024, 3, 15)) is not None
    assert table.find_row("FGSZ", EIC, "Entry", date(2025, 9, 30)) is not None
    assert table.find_row("FGSZ", EIC, "Entry", date(2025, 10, 1)) is None


def test_open_ended_row_applies_to_later_dates():
    table = make_table(make_row(valid_from="2026-10-01", valid_to=None))
    row = table.find_row("FGSZ", EIC, "Entry", date(2029, 5, 10))
    assert row is not None and row.open_ended
    assert table.find_row("FGSZ", EIC, "Entry", date(2026, 9, 30)) is None


def test_date_before_earliest_row_has_no_tariff():
    table = make_table(make_row(valid_from="2025-10-01"))
    assert table.find_row("FGSZ", EIC, "Entry", date(2024, 1, 1)) is None
    assert table.earliest_valid_from("FGSZ", EIC, "Entry") == date(2025, 10, 1)
    assert table.earliest_valid_from("FGSZ", "nope", "Entry") is None


def test_direction_is_part_of_the_key():
    table = make_table(make_row(direction="Entry", prices={"Year": 1.0}), make_row(direction="Exit", prices={"Year": 2.0}))
    assert table.find_row("FGSZ", EIC, "Entry", date(2026, 1, 1)).year_price() == 1
    assert table.find_row("FGSZ", EIC, "Exit", date(2026, 1, 1)).year_price() == 2


def test_later_row_supersedes_an_open_ended_one():
    table = make_table(
        make_row(valid_from="2026-10-01", valid_to=None, prices={"Year": 1.0}),
        make_row(valid_from="2027-10-01", valid_to=None, prices={"Year": 2.0}),
    )
    assert table.find_row("FGSZ", EIC, "Entry", date(2027, 6, 1)).year_price() == 1
    assert table.find_row("FGSZ", EIC, "Entry", date(2028, 1, 1)).year_price() == 2


# --- 3.5 source report ------------------------------------------------------------

def test_source_text():
    open_row = make_table(make_row(valid_from="2026-10-01", valid_to=None)).find_row("FGSZ", EIC, "Entry", date(2027, 1, 1))
    closed_row = make_table(make_row()).find_row("FGSZ", EIC, "Entry", date(2026, 1, 1))
    assert open_row.source_text() == "from 2026-10-01 (open-ended)"
    assert closed_row.source_text() == "from 2025-10-01"


# --- 3.6 configured path -------------------------------------------------------------

def test_default_path_is_the_committed_real_file_and_loads():
    path = resolve_tariff_path({})
    assert path == tariffs.DEFAULT_PATH and path.name == "tariffs_real.xlsx" and path.exists()
    result = load_tariffs(path)
    assert result.ok and len(result.table) > 0


def test_configured_sample_file_is_used():
    path = resolve_tariff_path({tariffs.PATH_ENV_VAR: str(tariffs.DEFAULT_SAMPLE_PATH)})
    assert path == tariffs.DEFAULT_SAMPLE_PATH and load_tariffs(path).ok


def test_environment_variable_points_at_another_file(tmp_path):
    other = tmp_path / "other.xlsx"
    make_frame(make_row(eic="ONLYHERE")).to_excel(other, sheet_name="Capacity_fee", index=False)
    path = resolve_tariff_path({tariffs.PATH_ENV_VAR: str(other)})
    assert path == other
    assert load_tariffs(path).table.keys() == [("FGSZ", "ONLYHERE", "Entry")]
    assert resolve_tariff_path({tariffs.PATH_ENV_VAR: "  "}) == tariffs.DEFAULT_PATH


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


# --- products across tariff changes ---------------------------------------------------------------

def calendar_year_table():
    return make_table(
        make_row(operator="GCA", currency="EUR", valid_from="2026-01-01", valid_to="2026-12-31", prices={"Year": 3.97}),
        make_row(operator="GCA", currency="EUR", valid_from="2027-01-01", valid_to=None, prices={"Year": 4.10}),
    )


def test_gas_year_across_a_1_january_tariff_change():
    table = calendar_year_table()
    price, parts = table.product_price("GCA", EIC, "Entry", date(2026, 10, 1), date(2027, 9, 30),
                                       lambda row: row.year_price())
    assert price == Fraction("3.97") * 92 / 365 + Fraction("4.10") * 273 / 365
    assert f"{float(price):.6f}" == "4.067233"
    assert [(p.first, p.last, p.days, p.row.year_price()) for p in parts] == [
        (date(2026, 10, 1), date(2026, 12, 31), 92, Fraction("3.97")),
        (date(2027, 1, 1), date(2027, 9, 30), 273, Fraction("4.1")),
    ]


def test_quarter_across_a_mid_quarter_tariff_change():
    table = make_table(
        make_row(operator="EUSTR", currency="EUR", valid_from="2026-01-01", valid_to="2026-04-30", prices={"Q2_Apr": 1.20}),
        make_row(operator="EUSTR", currency="EUR", valid_from="2026-05-01", valid_to=None, prices={"Q2_Apr": 1.32}),
    )
    price, parts = table.product_price("EUSTR", EIC, "Entry", date(2026, 4, 1), date(2026, 6, 30),
                                       lambda row: row.quarter_price(2))
    assert price == Fraction("1.20") * 30 / 91 + Fraction("1.32") * 61 / 91
    assert [p.days for p in parts] == [30, 61]


def test_product_with_one_row_is_the_cell_itself():
    table = make_table(make_row(valid_from="2025-10-01", valid_to=None, prices={"Year": 1234.5}))
    price, parts = table.product_price("FGSZ", EIC, "Entry", date(2026, 10, 1), date(2027, 9, 30),
                                       lambda row: row.year_price())
    assert price == Fraction("1234.5") and len(parts) == 1


def test_open_ended_row_superseded_inside_the_period():
    table = make_table(
        make_row(valid_from="2025-10-01", valid_to=None, prices={"Year": 1.0}),
        make_row(valid_from="2027-04-01", valid_to=None, prices={"Year": 2.0}),
    )
    parts = table.product_parts("FGSZ", EIC, "Entry", date(2026, 10, 1), date(2027, 9, 30))
    assert [(p.first, p.last, p.row.year_price()) for p in parts] == [
        (date(2026, 10, 1), date(2027, 3, 31), 1), (date(2027, 4, 1), date(2027, 9, 30), 2),
    ]


def test_a_day_without_a_row_has_no_price():
    table = make_table(make_row(valid_from="2026-01-01", valid_to="2026-12-31"))
    try:
        table.product_parts("FGSZ", EIC, "Entry", date(2026, 10, 1), date(2027, 9, 30))
    except tariffs.NoTariffRow as error:
        assert error.day == date(2027, 1, 1)
    else:
        raise AssertionError("expected NoTariffRow")
