from datetime import date

import pytest

from core import points
from core.points import BULGARTRANSGAZ, FGSZ, GASTRANS
from core.tariffs import load_tariffs, resolve_tariff_path

from .helpers import make_row, make_table

EXCLUDED_EICS = {
    "21W000000000087M",   # Egyesített Kitárolás (virtual storage)
    "39ZSZOREG1--FGTZ",   # UGS-2-SZOREG
    "39WKETELJCS57EN5",   # MOL Nyrt KTD
    "39WKEMEHKER1NNNV",   # Méhkerék "0" pont
    "TSO_EXIT_SUM_HU",    # n.a domestic exit sum
    "21W000000000031C",   # UGS Chiren (Bulgartransgaz storage)
}


def find(tso, name, flow):
    return next(p for p in points.POINTS if (p.tso, p.name, p.flow) == (tso, name, flow))


def describe(route):
    return [(p.tso, p.direction, p.cleaned_name) for p in route]


# --- supported points ----------------------------------------------------------------------

def test_point_counts_per_tso():
    assert [len(points.points_of(tso)) for tso in points.TSOS] == [13, 4, 13]
    assert len(points.POINTS) == 30


def test_excluded_points_are_absent():
    assert not EXCLUDED_EICS & {p.eic for p in points.POINTS}
    assert ("Mosonmagyaróvár", "HU>AT") not in {(p.name, p.flow) for p in points.POINTS}


def test_tab2_labels_are_unique_per_tso_and_include_the_flow():
    for tso in points.TSOS:
        labels = [p.fee_label() for p in points.points_of(tso)]
        assert len(set(labels)) == len(labels)
    labels = [p.fee_label() for p in points.points_of(FGSZ)]
    assert "Csanádpalota RO>HU (21Z000000000236Q)" in labels
    assert "Csanádpalota HU>RO (21Z000000000236Q)" in labels


def test_interruptible_label():
    point = find(FGSZ, "Kiskundorozsma 2", "HU>RS")
    assert point.fee_label("Interruptible") == "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible"
    assert point.fee_label("Firm") == "Kiskundorozsma 2 HU>RS (21Z000000000505P)"


def test_cleaned_names_and_tso_names():
    assert "Beregdaróc (UA>HU)" in {p.cleaned_name for p in points.POINTS}  # no "1400"
    assert not any("1400" in p.name for p in points.POINTS)
    assert [points.tso_name(t) for t in points.TSOS] == ["FGSZ", "Gastrans", "Bulgartransgaz"]


# --- point identity ------------------------------------------------------------------------

def test_same_eic_in_both_directions_matches_separate_rows():
    entry, exit_ = find(FGSZ, "Balassagyarmat", "SK>HU"), find(FGSZ, "Balassagyarmat", "HU>SK")
    assert entry.eic == exit_.eic
    table = make_table(
        make_row(eic=entry.eic, direction="Entry", name="Balassagyarmat/Velké Zlievce - HU (SK>HU)", prices={"Year": 1.0}),
        make_row(eic=entry.eic, direction="Exit", name="Balassagyarmat (HU>SK) MGT", prices={"Year": 2.0}),
    )
    assert table.find_row(*entry.key, date(2026, 1, 1)).year_price() == 1
    assert table.find_row(*exit_.key, date(2026, 1, 1)).year_price() == 2


def test_look_alike_names_are_different_points():
    exit_k = find(FGSZ, "Kiskundorozsma", "HU>RS")
    entry_k2 = find(FGSZ, "Kiskundorozsma 2", "RS>HU")
    assert exit_k.eic != entry_k2.eic and exit_k.key != entry_k2.key


def test_two_sides_of_one_border_are_two_points():
    gastrans_exit, fgsz_entry = find(GASTRANS, "Kiskundorozsma 2", "RS>HU"), find(FGSZ, "Kiskundorozsma 2", "RS>HU")
    assert gastrans_exit.eic == fgsz_entry.eic and gastrans_exit.key != fgsz_entry.key


# --- corridor ------------------------------------------------------------------------------

def test_crossings():
    assert describe(points.crossing("RS", "HU")) == [
        (GASTRANS, "Exit", "Kiskundorozsma 2 (RS>HU)"), (FGSZ, "Entry", "Kiskundorozsma 2 (RS>HU)"),
    ]
    hu_rs = points.crossing("HU", "RS")
    assert describe(hu_rs) == [(FGSZ, "Exit", "Kiskundorozsma 2 (HU>RS)"), (GASTRANS, "Entry", "Kiskundorozsma 2 (HU>RS)")]
    assert "21Z000000000154S" not in {p.eic for p in hu_rs}


@pytest.mark.parametrize("begin,end,expected", [
    ("BG", "HU", [(BULGARTRANSGAZ, "Exit", "Kireevo/Zaychar (BG>RS)"), (GASTRANS, "Entry", "Kireevo/Zaychar (BG>RS)"),
                  (GASTRANS, "Exit", "Kiskundorozsma 2 (RS>HU)"), (FGSZ, "Entry", "Kiskundorozsma 2 (RS>HU)")]),
    ("BG", "RS", [(BULGARTRANSGAZ, "Exit", "Kireevo/Zaychar (BG>RS)"), (GASTRANS, "Entry", "Kireevo/Zaychar (BG>RS)")]),
    ("RS", "HU", [(GASTRANS, "Exit", "Kiskundorozsma 2 (RS>HU)"), (FGSZ, "Entry", "Kiskundorozsma 2 (RS>HU)")]),
    ("HU", "RS", [(FGSZ, "Exit", "Kiskundorozsma 2 (HU>RS)"), (GASTRANS, "Entry", "Kiskundorozsma 2 (HU>RS)")]),
    ("RS", "BG", [(GASTRANS, "Exit", "Kireevo/Zaychar (RS>BG)"), (BULGARTRANSGAZ, "Entry", "Kireevo/Zaychar (RS>BG)")]),
    ("HU", "BG", [(FGSZ, "Exit", "Kiskundorozsma 2 (HU>RS)"), (GASTRANS, "Entry", "Kiskundorozsma 2 (HU>RS)"),
                  (GASTRANS, "Exit", "Kireevo/Zaychar (RS>BG)"), (BULGARTRANSGAZ, "Entry", "Kireevo/Zaychar (RS>BG)")]),
])
def test_route_points_for_every_country_pair(begin, end, expected):
    assert describe(points.route_points(begin, end)) == expected


@pytest.mark.parametrize("begin,end", [("HU", "HU"), ("BG", "BG"), ("AT", "HU"), ("HU", "")])
def test_same_or_unknown_country_is_not_a_route(begin, end):
    with pytest.raises(ValueError):
        points.route_points(begin, end)


# --- the sample has rows for every point -------------------------------------------------------

INTERRUPTIBLE = {
    (FGSZ, "Kiskundorozsma 2", "HU>RS"),
    (GASTRANS, "Kiskundorozsma 2", "HU>RS"),
    (GASTRANS, "Kireevo/Zaychar", "RS>BG"),
}


def test_every_point_has_rows_of_the_expected_capacity_type_in_the_sample():
    table = load_tariffs(resolve_tariff_path({})).table
    for point in points.POINTS:
        expected = "Interruptible" if (point.tso, point.name, point.flow) in INTERRUPTIBLE else "Firm"
        assert table.capacity_type(*point.key) == expected, point
        assert table.find_row(*point.key, date(2026, 10, 1)) is not None, point
