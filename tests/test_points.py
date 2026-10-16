from datetime import date

import pytest

from core import points
from core.points import BULGARTRANSGAZ, FGSZ, GASTRANS
from core import tariffs
from core.tariffs import load_tariffs

from .helpers import KNOWN_POINTS, make_row, make_table

EXCLUDED_EICS = {
    "21W000000000087M",   # Egyesített Kitárolás (virtual storage)
    "39ZSZOREG1--FGTZ",   # UGS-2-SZOREG
    "39WKETELJCS57EN5",   # MOL Nyrt KTD
    "39WKEMEHKER1NNNV",   # Méhkerék "0" pont
    "TSO_EXIT_SUM_HU",    # n.a domestic exit sum
    "21W000000000031C",   # UGS Chiren (Bulgartransgaz storage)
    "21Y000000000102O",   # Eustream Domestic
    "21Z0000000000600",   # Baumgarten (GCA), not WAG
    "21Z000000000164P",   # Baumgarten (TAG)
}


@pytest.fixture(scope="module")
def real():
    """The catalog of the real tariff file."""
    return points.build_catalog(load_tariffs(tariffs.DEFAULT_PATH).table)


def find(tso, name, flow):
    return next(p for p in KNOWN_POINTS if (p.tso, p.name, p.flow) == (tso, name, flow))


def describe(route):
    return [(p.tso, p.direction, p.cleaned_name) for p in route]


def single(catalog, tso, name, flow):
    return next(p for p in catalog.singles if (p.tso, p.name, p.flow) == (tso, name, flow))


def bundle(catalog, label):
    return next(b for b in catalog.bundles if b.label() == label)


# --- catalog ---------------------------------------------------------------------------------

def test_point_counts_per_tso(real):
    assert (len(real.singles), len(real.lng), len(real.bundles)) == (109, 14, 43)
    counts = {tso: len(real.singles_of(tso)) for tso in real.tsos()}
    assert (counts[FGSZ], counts[BULGARTRANSGAZ], counts[GASTRANS]) == (14, 13, 4)


def test_excluded_points_are_absent(real):
    every = [*real.singles, *real.lng]
    assert not EXCLUDED_EICS & {p.eic for p in every}
    assert not any(p.tso == "TAG" and p.name == "Baumgarten" for p in every)


def test_interruptible_only_side_is_still_a_single_side(real):
    point = single(real, FGSZ, "Mosonmagyaróvár", "HU>AT")
    assert real.capacity_type(point) == "Interruptible"
    assert point.fee_label(real.capacity_type(point)) == "Mosonmagyaróvár HU>AT (21Z000000000003C) - Interruptible"


def test_lng_entries(real):
    assert [p.lng_label() for p in real.lng] == [
        "Agia Triada (DESFA)", "Amfitriti (DESFA)", "Brunsbüttel Hafen (Gasunie Deutschland)",
        "Cavarzere (Snam Rete Gas)", "Eems Energy Terminal (Gasunie Transport Services)",
        "Gate Terminal (Gasunie Transport Services)", "Klaipeda (Amber Grid)", "Omišalj (Plinacro)",
        "Panigaglia (Snam Rete Gas)", "Piombino (Snam Rete Gas)", "Ravenna (Snam Rete Gas)",
        "Stade Hafen (Gasunie Deutschland)", "Wilhelmshaven (Open Grid Europe)", "Świnoujście (GAZ-SYSTEM)",
    ]


def test_every_cleaned_name_and_flow_on_the_real_file(real):
    """Any change to the cleaning rule shows up here."""
    names = sorted({(p.name, p.flow) for p in real.singles})
    assert names == [
        ("Balassagyarmat", "HU>SK"), ("Balassagyarmat", "SK>HU"), ("Baumgarten", "AT>SK"), ("Baumgarten", "SK>AT"),
        ("Beregdaróc", "UA>HU"), ("Cieszyn", "CZ>PL"), ("Cieszyn", "PL>CZ"), ("Csanádpalota", "HU>RO"),
        ("Csanádpalota", "RO>HU"), ("Drávaszerdahely", "CR>HU"), ("Drávaszerdahely", "HU>CR"),
        ("GCP GAZ-SYSTEM/UA TSO", "PL>UA"), ("GCP GAZ-SYSTEM/UA TSO", "UA>PL"), ("Gorizia/Šempeter", "IT>SI"),
        ("Gorizia/Šempeter", "SI>IT"), ("Kipi", "TR>GR"), ("Kipoi", "TR>TAP"), ("Kireevo/Zaychar", "BG>RS"),
        ("Kireevo/Zaychar", "RS>BG"), ("Kiskundorozsma", "HU>RS"), ("Kiskundorozsma 2", "HU>RS"),
        ("Kiskundorozsma 2", "RS>HU"), ("Komotini", "DESFA>IGB"), ("Komotini", "TAP>ICGB"),
        ("Kulata/Sidirokastron", "BG>GR"), ("Kulata/Sidirokastron", "GR>BG"), ("Kyustendil/Zidilovo", "BG>MK"),
        ("Lanžhot", "CZ>SK"), ("Lanžhot", "SK>CZ"), ("Mazara del Vallo", "LY>IT"), ("Melendugno", "TAP>IT"),
        ("Mosonmagyaróvár", "AT>HU"), ("Mosonmagyaróvár", "HU>AT"), ("Murfeld/Ceršak", "AT>SI"),
        ("Murfeld/Ceršak", "SI>AT"), ("Nea Mesimvria", "GR>TAP"), ("Nea Mesimvria", "TAP>GR"),
        ("Negru Voda 1/Kardam", "BG>RO"), ("Negru Voda 1/Kardam", "RO>BG"), ("Rogatec", "CR>SI"),
        ("Rogatec", "SI>CR"), ("Ruse/Giurgiu", "BG>RO"), ("Ruse/Giurgiu", "RO>BG"), ("Santaka", "LT>PL"),
        ("Stara Zagora", "ICGB>BG"), ("Strandzha 1/Malkoclar", "BG>TR"), ("Strandzha 1/Malkoclar", "TR>BG"),
        ("Strandzha 2/Malkoclar", "TR>BG"), ("Tarvisio/Arnoldstein", "AT>IT"), ("Tarvisio/Arnoldstein", "IT>AT"),
        ("Uzhgorod/Velké Kapušany", "SK>UA"), ("Uzhgorod/Velké Kapušany", "UA>SK"), ("VIP Bereg", "HU>UA"),
        ("VIP Bereg", "UA>HU"), ("VIP Brandov-GASPOOL", "CZ>DE"), ("VIP Brandov-GASPOOL", "DE>CZ"),
        ("VIP Oberkappel", "AT>DE"), ("VIP Oberkappel", "DE>AT"), ("VIP TTF-THE-H", "DE>NL"),
        ("VIP TTF-THE-H", "NL>DE"), ("Vyrava", "PL>SK"), ("Vyrava", "SK>PL"),
    ]


def test_known_points_keep_their_names_in_the_catalog(real):
    assert set(KNOWN_POINTS) <= set(real.singles)


@pytest.mark.parametrize("source,expected", [
    ("Csanádpalota - RO (RO>HU)", ("Csanádpalota", "RO>HU")),
    ("Baumgarten - AT (AT>SK, WAG)", ("Baumgarten", "AT>SK")),
    ("Murfeld/Cersak - AT (SI>AT) virtuális", ("Murfeld/Cersak", "SI>AT")),
    ("Uzhgorod/Velké Kapušany SK (SK>UA)", ("Uzhgorod/Velké Kapušany", "SK>UA")),
    ("Stara Zagora ICGB (ICGB>BG)", ("Stara Zagora", "ICGB>BG")),
    ("Nea Mesimvria – GR (TAP>GR)", ("Nea Mesimvria", "TAP>GR")),
    ("Kipoi TR>TAP", ("Kipoi", "TR>TAP")),
    ("Wilhelmshaven, LNG-Zone - DE (LNG>DE)", ("Wilhelmshaven", "LNG>DE")),
    ("Brunsbüttel Hafen (FSRU) - DE (LNG>DE)", ("Brunsbüttel Hafen", "LNG>DE")),
    ("Mazara del Vallo", None),
])
def test_clean_name(source, expected):
    assert points.clean_name(source) == expected


# --- bundles ---------------------------------------------------------------------------------

def test_bundle_sides(real):
    moson = bundle(real, "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)")
    assert [(p.tso, p.direction, p.eic) for p in moson.sides] == [
        ("GCA", "Exit", "21Z000000000003C"), (FGSZ, "Entry", "21Z000000000003C"),
    ]
    assert moson.exit.name == moson.entry.name == "Mosonmagyaróvár"


def test_interruptible_crossings_are_not_bundled(real):
    pairs = {(b.name, b.flow) for b in real.bundles}
    for crossing in [("Mosonmagyaróvár", "HU>AT"), ("Kiskundorozsma 2", "HU>RS"), ("Murfeld/Ceršak", "SI>AT"),
                     ("Kireevo/Zaychar", "RS>BG")]:
        assert crossing not in pairs


def test_baumgarten_bundles_use_wag(real):
    baumgarten = [b for b in real.bundles if b.name == "Baumgarten"]
    assert [b.label() for b in baumgarten] == [
        "Baumgarten AT>SK (Gas Connect Austria + Eustream)", "Baumgarten SK>AT (Eustream + Gas Connect Austria)",
    ]
    assert {p.eic for b in baumgarten for p in b.sides} == {"21Y---A001A023-Y", "21Z000000000163R"}


def test_bundles_need_both_sides_firm():
    eic = "21Z000000000003C"
    table = make_table(
        make_row(eic=eic, direction="Exit", operator="GCA", currency="EUR", name="Mosonmagyaróvár - AT (AT>HU)"),
        make_row(eic=eic, direction="Entry", name="Mosonmagyaróvár - HU (AT>HU)"),
        make_row(eic=eic, direction="Exit", name="Mosonmagyaróvár - HU (HU>AT)", capacity="Interruptible"),
        make_row(eic=eic, direction="Entry", operator="GCA", currency="EUR", name="Mosonmagyaróvár - AT (HU>AT)"),
    )
    catalog = points.build_catalog(table)
    assert [b.label() for b in catalog.bundles] == ["Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)"]
    assert len(catalog.singles) == 4


# --- labels and TSOs -------------------------------------------------------------------------

def test_tab2_labels_are_unique_per_tso_and_include_the_flow(real):
    for tso in real.tsos():
        labels = [p.fee_label() for p in real.singles_of(tso)]
        assert len(set(labels)) == len(labels)
    labels = [p.fee_label() for p in real.singles_of(FGSZ)]
    assert "Csanádpalota RO>HU (21Z000000000236Q)" in labels
    assert "Csanádpalota HU>RO (21Z000000000236Q)" in labels


def test_interruptible_label(real):
    labels = [p.fee_label(real.capacity_type(p)) for p in real.singles_of(GASTRANS)]
    assert [label.endswith(" - Interruptible") for label in labels] == [False, True, True, False]
    point = find(FGSZ, "Kiskundorozsma 2", "HU>RS")
    assert point.fee_label("Interruptible") == "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible"
    assert point.fee_label("Firm") == "Kiskundorozsma 2 HU>RS (21Z000000000505P)"


def test_cleaned_names_and_tso_names(real):
    assert "Beregdaróc (UA>HU)" in {p.cleaned_name for p in real.singles}  # no "1400"
    assert not any("1400" in p.name for p in real.singles)
    assert len(real.tsos()) == 21
    assert {"Eustream", "Gas Connect Austria", "Open Grid Europe", "Snam Rete Gas"} <= {
        points.tso_name(t) for t in real.tsos()}


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


# --- network (tab 1) ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def network(real):
    return points.build_network(real)


def label(network, name):
    return next(p.label for p in network.points if p.name == name)


def route(network, begin, *names):
    return begin, [label(network, name) for name in names]


def test_map_points_on_the_real_file(network):
    assert network.countries == ("AT", "BG", "CR", "CZ", "DE", "GR", "HU", "IT", "NL", "PL", "RO", "RS", "SI", "SK", "UA")
    assert sorted(p.name for p in network.points) == sorted([
        "Mosonmagyaróvár", "VIP Oberkappel", "Tarvisio/Arnoldstein", "Murfeld/Ceršak", "Baumgarten",
        "Kulata/Sidirokastron", "Negru Voda 1/Kardam", "Ruse/Giurgiu", "Kireevo/Zaychar", "Drávaszerdahely",
        "Rogatec", "VIP Brandov-GASPOOL", "Cieszyn", "Lanžhot", "VIP TTF-THE-H", "Csanádpalota",
        "Kiskundorozsma 2", "Balassagyarmat", "VIP Bereg", "Gorizia/Šempeter", "Vyrava", "Uzhgorod/Velké Kapušany",
    ])
    assert not {"Stara Zagora", "Komotini", "Nea Mesimvria"} & {p.name for p in network.points}


def test_crossing_at_a_point_with_two_tsos_in_one_country(network):
    tarvisio = network.point(label(network, "Tarvisio/Arnoldstein")).crossing_from("AT")
    assert (tarvisio.exit.tso, tarvisio.entry.tso, tarvisio.exit.flow) == ("TAG", "snam", "AT>IT")
    moson = network.point(label(network, "Mosonmagyaróvár")).crossing_from("HU")
    assert moson.entry.tso == "GCA"


def test_points_without_a_partner_are_not_map_points(network):
    names = {p.name for p in network.points}
    assert not {"Kiskundorozsma", "GCP GAZ-SYSTEM/UA TSO", "Beregdaróc", "Kipi", "Strandzha 1/Malkoclar",
                "Kyustendil/Zidilovo", "Mazara del Vallo"} & names
    assert "PL" not in {p.crossing_from("UA").to_country for p in network.points_from("UA")}


def test_two_points_on_one_border(network):
    from_bg = {p.name for p in network.points_from("BG")}
    assert {"Negru Voda 1/Kardam", "Ruse/Giurgiu", "Kireevo/Zaychar", "Kulata/Sidirokastron"} == from_bg


@pytest.mark.parametrize("begin,names,expected", [
    ("BG", ("Kireevo/Zaychar", "Kiskundorozsma 2"), [
        (BULGARTRANSGAZ, "Exit", "Kireevo/Zaychar (BG>RS)"), (GASTRANS, "Entry", "Kireevo/Zaychar (BG>RS)"),
        (GASTRANS, "Exit", "Kiskundorozsma 2 (RS>HU)"), (FGSZ, "Entry", "Kiskundorozsma 2 (RS>HU)")]),
    ("RS", ("Kiskundorozsma 2",), [
        (GASTRANS, "Exit", "Kiskundorozsma 2 (RS>HU)"), (FGSZ, "Entry", "Kiskundorozsma 2 (RS>HU)")]),
    ("HU", ("Kiskundorozsma 2", "Kireevo/Zaychar"), [
        (FGSZ, "Exit", "Kiskundorozsma 2 (HU>RS)"), (GASTRANS, "Entry", "Kiskundorozsma 2 (HU>RS)"),
        (GASTRANS, "Exit", "Kireevo/Zaychar (RS>BG)"), (BULGARTRANSGAZ, "Entry", "Kireevo/Zaychar (RS>BG)")]),
    ("RS", ("Kireevo/Zaychar",), [
        (GASTRANS, "Exit", "Kireevo/Zaychar (RS>BG)"), (BULGARTRANSGAZ, "Entry", "Kireevo/Zaychar (RS>BG)")]),
    ("BG", ("Ruse/Giurgiu", "Csanádpalota"), [
        (BULGARTRANSGAZ, "Exit", "Ruse/Giurgiu (BG>RO)"), ("TRANSGA", "Entry", "Ruse/Giurgiu (BG>RO)"),
        ("TRANSGA", "Exit", "Csanádpalota (RO>HU)"), (FGSZ, "Entry", "Csanádpalota (RO>HU)")]),
    ("HU", ("Mosonmagyaróvár", "Tarvisio/Arnoldstein"), [
        (FGSZ, "Exit", "Mosonmagyaróvár (HU>AT)"), ("GCA", "Entry", "Mosonmagyaróvár (HU>AT)"),
        ("TAG", "Exit", "Tarvisio/Arnoldstein (AT>IT)"), ("snam", "Entry", "Tarvisio/Arnoldstein (AT>IT)")]),
])
def test_route_points(network, begin, names, expected):
    assert describe(points.route_crossing_points(network, *route(network, begin, *names))) == expected


def test_route_text_and_end(network):
    begin, labels = route(network, "BG", "Kireevo/Zaychar", "Kiskundorozsma 2")
    assert points.route_text(network, begin, labels) == "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"
    assert points.route_end(network, begin, labels) == "HU"
    assert points.route_end(network, "HU", []) == "HU"


def test_extend_route_adds_a_bordering_point(network):
    begin, labels = route(network, "BG", "Kireevo/Zaychar")
    assert [p.name for p in network.points_from("RS")] == ["Kireevo/Zaychar", "Kiskundorozsma 2"]
    extended = points.extend_route(network, begin, labels, label(network, "Kiskundorozsma 2"))
    assert points.route_text(network, begin, extended) == "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"


def test_point_not_on_the_current_country(network):
    with pytest.raises(points.RouteNotPossible, match=r"^Not possible: Vyrava \(PL - SK\) does not border BG\.$"):
        points.extend_route(network, "BG", [], label(network, "Vyrava"))


def test_entering_a_country_a_second_time(network):
    begin, labels = route(network, "HU", "Balassagyarmat", "Baumgarten")
    with pytest.raises(points.RouteNotPossible, match="would enter HU a second time"):
        points.extend_route(network, begin, labels, label(network, "Mosonmagyaróvár"))


@pytest.mark.parametrize("begin", ["TAP", "LT", ""])
def test_unknown_beginning_is_not_possible(network, begin):
    with pytest.raises(points.RouteNotPossible):
        points.walk(network, begin, [])


# --- the sample has rows for every point -------------------------------------------------------

INTERRUPTIBLE = {
    (FGSZ, "Kiskundorozsma 2", "HU>RS"),
    (GASTRANS, "Kiskundorozsma 2", "HU>RS"),
    (GASTRANS, "Kireevo/Zaychar", "RS>BG"),
}


def test_every_point_has_rows_of_the_expected_capacity_type_in_the_sample():
    table = load_tariffs(tariffs.DEFAULT_SAMPLE_PATH).table
    for point in KNOWN_POINTS:
        expected = "Interruptible" if (point.tso, point.name, point.flow) in INTERRUPTIBLE else "Firm"
        assert table.capacity_type(*point.key) == expected, point
        assert table.find_row(*point.key, date(2026, 10, 1)) is not None, point
