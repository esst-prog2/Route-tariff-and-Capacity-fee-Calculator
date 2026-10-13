"""The point catalog built from the loaded tariff rows (single sides, LNG
entries and bundled border points), and the HU - RS - BG corridor that tab 1
routes run along.

A point is identified by TSO, EIC and direction, never by the raw `Network
point` text: one EIC covers both directions of a border point and both TSOs'
sides of it. The source names are inconsistent, so the shown name and flow
come from a cleaning rule, with an override table for the names the rule
cannot clean."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from .tariffs import FIRM, INTERRUPTIBLE, TSO_NAMES, TariffTable

ENTRY = "Entry"
EXIT = "Exit"

FGSZ = "FGSZ"
GASTRANS = "Gastran"  # the codes used in the tariff file's `System operator` column
BULGARTRANSGAZ = "BGTRGAZ"
EUSTREAM = "EUSTR"
GCA = "GCA"
TAG = "TAG"


def tso_name(tso: str) -> str:
    return TSO_NAMES.get(tso, tso)


@dataclass(frozen=True)
class Point:
    tso: str  # source operator code, e.g. "Gastran"
    name: str  # cleaned name, e.g. "Csanádpalota"
    flow: str  # border crossing direction, e.g. "RO>HU"
    eic: str
    direction: str  # ENTRY or EXIT

    @property
    def key(self) -> tuple[str, str, str]:
        """How the point is matched to tariff rows."""
        return self.tso, self.eic, self.direction

    @property
    def tso_name(self) -> str:
        return tso_name(self.tso)

    @property
    def cleaned_name(self) -> str:
        return f"{self.name} ({self.flow})"

    @property
    def is_lng(self) -> bool:
        return self.direction == ENTRY and self.flow.startswith("LNG>")

    def fee_label(self, capacity_type: str | None = None) -> str:
        """Tab 2 single-side label: the flow is included so a TSO's labels are unique."""
        label = f"{self.name} {self.flow} ({self.eic})"
        return f"{label} - Interruptible" if capacity_type == INTERRUPTIBLE else label

    def lng_label(self) -> str:
        return f"{self.name} ({self.tso_name})"


@dataclass(frozen=True)
class Bundle:
    """One TSO's exit and the neighbouring TSO's entry at the same border and flow."""

    exit: Point
    entry: Point

    @property
    def name(self) -> str:
        return self.entry.name

    @property
    def flow(self) -> str:
        return self.entry.flow

    @property
    def sides(self) -> tuple[Point, Point]:
        return self.exit, self.entry

    def label(self) -> str:
        return f"{self.name} {self.flow} ({self.exit.tso_name} + {self.entry.tso_name})"


# Points the app knew before the catalog was built from the data. Their names are fixed here
# (they win over the cleaning rule, also for the other TSO's side of the same EIC), and the
# tab 1 corridor uses them.
POINTS: tuple[Point, ...] = (
    Point(FGSZ, "Mosonmagyaróvár", "AT>HU", "21Z000000000003C", ENTRY),
    Point(FGSZ, "Beregdaróc", "UA>HU", "21Z000000000139O", ENTRY),
    Point(FGSZ, "Csanádpalota", "RO>HU", "21Z000000000236Q", ENTRY),
    Point(FGSZ, "Drávaszerdahely", "CR>HU", "21Z000000000249H", ENTRY),
    Point(FGSZ, "Balassagyarmat", "SK>HU", "21Z000000000358C", ENTRY),
    Point(FGSZ, "Kiskundorozsma 2", "RS>HU", "21Z000000000505P", ENTRY),
    Point(FGSZ, "VIP Bereg", "UA>HU", "21Z000000000507L", ENTRY),
    Point(FGSZ, "Balassagyarmat", "HU>SK", "21Z000000000358C", EXIT),
    Point(FGSZ, "Csanádpalota", "HU>RO", "21Z000000000236Q", EXIT),
    Point(FGSZ, "Drávaszerdahely", "HU>CR", "21Z000000000249H", EXIT),
    Point(FGSZ, "Kiskundorozsma", "HU>RS", "21Z000000000154S", EXIT),
    Point(FGSZ, "Kiskundorozsma 2", "HU>RS", "21Z000000000505P", EXIT),
    Point(FGSZ, "VIP Bereg", "HU>UA", "21Z000000000507L", EXIT),
    Point(GASTRANS, "Kireevo/Zaychar", "BG>RS", "58Z-000000007-KZ", ENTRY),
    Point(GASTRANS, "Kiskundorozsma 2", "HU>RS", "21Z000000000505P", ENTRY),
    Point(GASTRANS, "Kiskundorozsma 2", "RS>HU", "21Z000000000505P", EXIT),
    Point(GASTRANS, "Kireevo/Zaychar", "RS>BG", "58Z-000000007-KZ", EXIT),
    Point(BULGARTRANSGAZ, "Kireevo/Zaychar", "RS>BG", "58Z-000000007-KZ", ENTRY),
    Point(BULGARTRANSGAZ, "Kulata/Sidirokastron", "GR>BG", "21Z000000000020C", ENTRY),
    Point(BULGARTRANSGAZ, "Strandzha 1/Malkoclar", "TR>BG", "21Z000000000157M", ENTRY),
    Point(BULGARTRANSGAZ, "Negru Voda 1/Kardam", "RO>BG", "21Z000000000159I", ENTRY),
    Point(BULGARTRANSGAZ, "Ruse/Giurgiu", "RO>BG", "21Z0000000002798", ENTRY),
    Point(BULGARTRANSGAZ, "Strandzha 2/Malkoclar", "TR>BG", "58Z-00000015-S2M", ENTRY),
    Point(BULGARTRANSGAZ, "Stara Zagora", "ICGB>BG", "58Z-IP-00034-STZ", ENTRY),
    Point(BULGARTRANSGAZ, "Kireevo/Zaychar", "BG>RS", "58Z-000000007-KZ", EXIT),
    Point(BULGARTRANSGAZ, "Kulata/Sidirokastron", "BG>GR", "21Z000000000020C", EXIT),
    Point(BULGARTRANSGAZ, "Kyustendil/Zidilovo", "BG>MK", "21Z000000000137S", EXIT),
    Point(BULGARTRANSGAZ, "Strandzha 1/Malkoclar", "BG>TR", "21Z000000000157M", EXIT),
    Point(BULGARTRANSGAZ, "Negru Voda 1/Kardam", "BG>RO", "21Z000000000159I", EXIT),
    Point(BULGARTRANSGAZ, "Ruse/Giurgiu", "BG>RO", "21Z0000000002798", EXIT),
)

# --- the catalog built from the tariff rows (tab 2) ------------------------------------------

# Storage, production and domestic points, and the Baumgarten points other than WAG.
EXCLUDED: frozenset[tuple[str, str]] = frozenset({
    (FGSZ, "21W000000000087M"),  # Egyesített Kitárolás
    (FGSZ, "39WKETELJCS57EN5"),  # MOL Nyrt KTD
    (FGSZ, "39WKEMEHKER1NNNV"),  # Méhkerék "0" pont
    (FGSZ, "39ZSZOREG1--FGTZ"),  # UGS-2-SZOREG
    (FGSZ, "TSO_EXIT_SUM_HU"),  # n.a (domestic exit sum)
    (BULGARTRANSGAZ, "21W000000000031C"),  # UGS Chiren
    (EUSTREAM, "21Y000000000102O"),  # Domestic
    (GCA, "21Z0000000000600"),  # Baumgarten (GCA), incl. the virtual AT->SK exit
    (TAG, "21Z000000000164P"),  # Baumgarten (TAG)
})

# Names (per EIC) and flows the cleaning rule cannot produce, and spellings fixed by hand.
EIC_NAMES: dict[str, str] = {
    "21Z000000000239K": "Cieszyn",
    "21Z0019743987060": "VIP TTF-THE-H",
    "21Z0000000002212": "Gate Terminal",
    "37Z0000000088623": "Stade Hafen",
    "21Z000000000454G": "Świnoujście",
    "21Z000000000510W": "Omišalj",
    "21Z0000000000058": "Murfeld/Ceršak",
    "21Z000000000044Z": "Gorizia/Šempeter",
    "21Z000000000061Z": "Lanžhot",
}
FLOW_OVERRIDES: dict[tuple[str, str, str], tuple[str, str]] = {  # key -> (name, flow)
    ("AMBERGR", "21Z0000000003697", ENTRY): ("Klaipeda", "LNG>LT"),
    ("snam", "21Z000000000080V", ENTRY): ("Mazara del Vallo", "LY>IT"),
    ("plinacr", "21Z000000000128T", EXIT): ("Rogatec", "CR>SI"),
}

# Bundles whose two sides have different EICs: Eustream's Baumgarten with Gas Connect Austria's WAG point.
EXTRA_BUNDLES: tuple[tuple[tuple[str, str, str], tuple[str, str, str]], ...] = (
    ((EUSTREAM, "21Y---A001A023-Y", EXIT), (GCA, "21Z000000000163R", ENTRY)),
    ((GCA, "21Z000000000163R", EXIT), (EUSTREAM, "21Y---A001A023-Y", ENTRY)),
)

_PAREN_FLOW = re.compile(r"\(([A-Z]+)\s*>\s*([A-Z]+)(?:,[^)]*)?\)")
_BARE_FLOW = re.compile(r"\b([A-Z]+)\s*-?>\s*([A-Z]+)\b")
_DROP_WORDS = re.compile(r"\s*(\(FSRU\)|,\s*LNG-Zone|\bvirtuális|\bvirtual)\s*", re.IGNORECASE)


def clean_name(source: str) -> tuple[str, str] | None:
    """(name, flow) from a source `Network point` text, or None when it has no flow."""
    text = source.strip()
    matches = list(_PAREN_FLOW.finditer(text))
    match = matches[-1] if matches else _BARE_FLOW.search(text)
    if match is None:
        return None
    flow = f"{match.group(1)}>{match.group(2)}"
    name = _DROP_WORDS.sub(" ", text[: match.start()]).strip()
    codes = {match.group(1), match.group(2)}
    while True:  # trailing country or operator codes, e.g. " - HU", " SK", " ICGB", " – GR"
        trailing = re.search(r"\s*[-–]?\s*\b([A-Z]{2,4})$", name)
        if trailing is None or not (trailing.group(1) in codes or len(trailing.group(1)) == 2):
            break
        name = name[: trailing.start()].rstrip(" -–")
    return name, flow


def _non_ascii(text: str) -> int:
    return sum(1 for c in unicodedata.normalize("NFC", text) if ord(c) > 127)


@dataclass(frozen=True)
class Catalog:
    singles: tuple[Point, ...]
    lng: tuple[Point, ...]
    bundles: tuple[Bundle, ...]
    capacity_types: dict[tuple[str, str, str], str]

    def tsos(self) -> list[str]:
        """TSOs that have at least one single side, by display name."""
        return sorted({p.tso for p in self.singles}, key=lambda t: tso_name(t).casefold())

    def singles_of(self, tso: str) -> list[Point]:
        return [p for p in self.singles if p.tso == tso]

    def capacity_type(self, point: Point) -> str | None:
        return self.capacity_types.get(point.key)


def build_catalog(table: TariffTable) -> Catalog:
    """Every usable point of the loaded rows, as single sides, LNG entries and bundles."""
    known = {p.key: p for p in POINTS}
    cleaned: dict[tuple[str, str, str], tuple[str, str]] = {}
    for key in table.keys():
        tso, eic, _ = key
        if (tso, eic) in EXCLUDED:
            continue
        if key in known:
            cleaned[key] = (known[key].name, known[key].flow)
        elif key in FLOW_OVERRIDES:
            cleaned[key] = FLOW_OVERRIDES[key]
        else:
            result = clean_name(table.network_point(*key))
            if result is not None:
                cleaned[key] = result

    # One name per EIC, so both sides of a border read the same: a fixed name, else the most
    # common cleaned one (the spelling with diacritics wins a tie).
    names: dict[str, str] = {}
    by_eic: dict[str, list[str]] = {}
    for (tso, eic, direction), (name, _) in cleaned.items():
        by_eic.setdefault(eic, []).append(name)
    for eic, candidates in by_eic.items():
        fixed = [p.name for p in POINTS if p.eic == eic]
        if eic in EIC_NAMES:
            names[eic] = EIC_NAMES[eic]
        elif fixed:
            names[eic] = Counter(fixed).most_common(1)[0][0]
        else:
            counts = Counter(candidates)
            names[eic] = max(counts, key=lambda n: (counts[n], _non_ascii(n), n))

    points: dict[tuple[str, str, str], Point] = {}
    for key, (name, flow) in cleaned.items():
        tso, eic, direction = key
        fixed = known.get(key)
        points[key] = fixed or Point(tso, names[eic] if key not in FLOW_OVERRIDES else name, flow, eic, direction)

    capacity_types = {key: table.capacity_type(*key) for key in points}
    order = lambda p: (tso_name(p.tso).casefold(), p.direction != ENTRY, p.name.casefold(), p.flow)
    singles = tuple(sorted((p for p in points.values() if not p.is_lng), key=order))
    lng = tuple(sorted((p for p in points.values() if p.is_lng), key=lambda p: (p.name.casefold(), p.tso)))

    firm = lambda p: capacity_types[p.key] == FIRM
    pairs = [
        Bundle(x, n) for x in singles if x.direction == EXIT
        for n in singles if n.direction == ENTRY and n.eic == x.eic and n.flow == x.flow and n.tso != x.tso
    ]
    pairs += [Bundle(points[x], points[n]) for x, n in EXTRA_BUNDLES if x in points and n in points]
    bundles = tuple(sorted(
        (b for b in pairs if firm(b.exit) and firm(b.entry)),
        key=lambda b: (b.name.casefold(), b.flow, tso_name(b.exit.tso), tso_name(b.entry.tso)),
    ))
    return Catalog(singles, lng, bundles, capacity_types)


# --- the HU - RS - BG corridor (tab 1) ------------------------------------------------------

COUNTRIES: tuple[str, ...] = ("HU", "RS", "BG")  # in corridor order
COUNTRY_TSO = {"HU": FGSZ, "RS": GASTRANS, "BG": BULGARTRANSGAZ}
BORDER_EICS = {
    frozenset({"HU", "RS"}): "21Z000000000505P",  # Kiskundorozsma 2
    frozenset({"RS", "BG"}): "58Z-000000007-KZ",  # Kireevo/Zaychar
}


def _point(tso: str, eic: str, direction: str, flow: str) -> Point:
    return next(p for p in POINTS if p.key == (tso, eic, direction) and p.flow == flow)


def crossing(from_country: str, to_country: str) -> list[Point]:
    """The exit of `from_country`'s TSO and the entry of `to_country`'s TSO
    at the border between two neighbouring countries."""
    eic = BORDER_EICS[frozenset({from_country, to_country})]
    flow = f"{from_country}>{to_country}"
    return [_point(COUNTRY_TSO[from_country], eic, EXIT, flow), _point(COUNTRY_TSO[to_country], eic, ENTRY, flow)]


def route_points(begin: str, end: str) -> list[Point]:
    """Hub to hub: the exit and entry at every border crossed, in route order.
    Raises ValueError for unknown countries or when begin == end."""
    if begin not in COUNTRIES or end not in COUNTRIES or begin == end:
        raise ValueError(f"no route from {begin} to {end}")
    i, j = COUNTRIES.index(begin), COUNTRIES.index(end)
    step = 1 if j > i else -1
    path = [COUNTRIES[k] for k in range(i, j + step, step)]
    return [p for a, b in zip(path, path[1:]) for p in crossing(a, b)]
