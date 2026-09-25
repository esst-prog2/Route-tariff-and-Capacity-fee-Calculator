from datetime import date

from core import points
from core.tariffs import load_tariffs, resolve_tariff_path

from .helpers import make_row, make_table

EXCLUDED_EICS = {
    "21W000000000087M",   # Egyesített Kitárolás (virtual storage)
    "39ZSZOREG1--FGTZ",   # UGS-2-SZOREG
    "39WKETELJCS57EN5",   # MOL Nyrt KTD
    "39WKEMEHKER1NNNV",   # Méhkerék "0" pont
    "TSO_EXIT_SUM_HU",    # n.a domestic exit sum
}


def test_seven_entries_and_five_exits():
    assert len(points.entries()) == 7
    assert len(points.exits()) == 5
    assert len(points.POINTS) == 12


def test_excluded_points_are_absent():
    assert not EXCLUDED_EICS & {p.eic for p in points.POINTS}
    # Interruptible-only exits from the sample
    assert ("Mosonmagyaróvár", "HU>AT") not in {(p.name, p.flow) for p in points.POINTS}
    assert ("Kiskundorozsma 2", "HU>RS") not in {(p.name, p.flow) for p in points.POINTS}


def test_tab2_labels_are_unique_and_include_the_direction():
    labels = [p.fee_label() for p in points.POINTS]
    assert len(set(labels)) == 12
    assert "Csanádpalota RO>HU (21Z000000000236Q)" in labels
    assert "Csanádpalota HU>RO (21Z000000000236Q)" in labels


def test_tab1_labels_are_unique_within_each_dropdown():
    for group in (points.entries(), points.exits()):
        labels = [p.route_label() for p in group]
        assert len(set(labels)) == len(labels)
    assert points.entries()[0].route_label() == "Mosonmagyaróvár (21Z000000000003C)"


def test_cleaned_names():
    assert "Beregdaróc (UA>HU)" in {p.cleaned_name for p in points.POINTS}  # no "1400"
    assert not any("1400" in p.name for p in points.POINTS)


def test_same_eic_in_both_directions_matches_separate_rows():
    balassagyarmat = [p for p in points.POINTS if p.name == "Balassagyarmat"]
    assert len(balassagyarmat) == 2 and balassagyarmat[0].eic == balassagyarmat[1].eic
    table = make_table(
        make_row(eic=balassagyarmat[0].eic, direction="Entry", name="Balassagyarmat/Velké Zlievce - HU (SK>HU)", prices={"Year": 1.0}),
        make_row(eic=balassagyarmat[0].eic, direction="Exit", name="Balassagyarmat (HU>SK) MGT", prices={"Year": 2.0}),
    )
    entry = next(p for p in balassagyarmat if p.direction == "Entry")
    exit_ = next(p for p in balassagyarmat if p.direction == "Exit")
    assert table.find_row(*entry.key, date(2026, 1, 1)).year_price() == 1
    assert table.find_row(*exit_.key, date(2026, 1, 1)).year_price() == 2


def test_look_alike_names_are_different_points():
    exit_k = next(p for p in points.exits() if p.name == "Kiskundorozsma")
    entry_k2 = next(p for p in points.entries() if p.name == "Kiskundorozsma 2")
    assert exit_k.eic != entry_k2.eic
    assert exit_k.key != entry_k2.key


def test_every_point_has_a_firm_row_on_2026_10_01_in_the_sample():
    result = load_tariffs(resolve_tariff_path({}))
    assert result.ok
    for point in points.POINTS:
        assert result.table.find_row(*point.key, date(2026, 10, 1)) is not None, point.cleaned_name


def test_tso_list_is_fgsz_only():
    assert points.TSOS == ("FGSZ",)
