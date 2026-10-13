"""The fixed list of cross-border points of the three supported TSOs, and the
HU - RS - BG corridor that tab 1 routes run along.

An explicit table, not derived from the raw `Network point` text: the source
names are inconsistent, while a point is reliably identified by TSO, EIC and
direction (one EIC covers both directions of a border point, and both TSOs'
sides of it)."""

from __future__ import annotations

from dataclasses import dataclass

ENTRY = "Entry"
EXIT = "Exit"

FGSZ = "FGSZ"
GASTRANS = "Gastran"  # the codes used in the tariff file's `System operator` column
BULGARTRANSGAZ = "BGTRGAZ"
TSOS: tuple[str, ...] = (FGSZ, GASTRANS, BULGARTRANSGAZ)
TSO_NAMES = {FGSZ: "FGSZ", GASTRANS: "Gastrans", BULGARTRANSGAZ: "Bulgartransgaz"}


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

    def fee_label(self, capacity_type: str | None = None) -> str:
        """Tab 2 label: the flow is included so a TSO's labels are unique."""
        label = f"{self.name} {self.flow} ({self.eic})"
        return f"{label} - Interruptible" if capacity_type == "Interruptible" else label


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


def points_of(tso: str) -> list[Point]:
    return [p for p in POINTS if p.tso == tso]


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
