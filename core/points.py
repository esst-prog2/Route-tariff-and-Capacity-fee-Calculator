"""The fixed list of FGSZ cross-border points the MVP offers.

An explicit table, not derived from the raw `Network point` text: the source
names are inconsistent, while a point is reliably identified by EIC plus
direction (one EIC covers both directions of a border point)."""

from __future__ import annotations

from dataclasses import dataclass

ENTRY = "Entry"
EXIT = "Exit"


@dataclass(frozen=True)
class Point:
    name: str  # cleaned name, e.g. "Csanádpalota"
    flow: str  # border crossing direction, e.g. "RO>HU"
    eic: str
    direction: str  # ENTRY or EXIT

    @property
    def key(self) -> tuple[str, str]:
        """How the point is matched to tariff rows."""
        return self.eic, self.direction

    @property
    def cleaned_name(self) -> str:
        return f"{self.name} ({self.flow})"

    def route_label(self) -> str:
        """Tab 1 label: entry and exit have separate dropdowns."""
        return f"{self.name} ({self.eic})"

    def fee_label(self) -> str:
        """Tab 2 label: the flow is included so all 12 labels are unique."""
        return f"{self.name} {self.flow} ({self.eic})"


POINTS: tuple[Point, ...] = (
    Point("Mosonmagyaróvár", "AT>HU", "21Z000000000003C", ENTRY),
    Point("Beregdaróc", "UA>HU", "21Z000000000139O", ENTRY),
    Point("Csanádpalota", "RO>HU", "21Z000000000236Q", ENTRY),
    Point("Drávaszerdahely", "CR>HU", "21Z000000000249H", ENTRY),
    Point("Balassagyarmat", "SK>HU", "21Z000000000358C", ENTRY),
    Point("Kiskundorozsma 2", "RS>HU", "21Z000000000505P", ENTRY),
    Point("VIP Bereg", "UA>HU", "21Z000000000507L", ENTRY),
    Point("Balassagyarmat", "HU>SK", "21Z000000000358C", EXIT),
    Point("Csanádpalota", "HU>RO", "21Z000000000236Q", EXIT),
    Point("Drávaszerdahely", "HU>CR", "21Z000000000249H", EXIT),
    Point("Kiskundorozsma", "HU>RS", "21Z000000000154S", EXIT),
    Point("VIP Bereg", "HU>UA", "21Z000000000507L", EXIT),
)

TSOS: tuple[str, ...] = ("FGSZ",)


def entries() -> list[Point]:
    return [p for p in POINTS if p.direction == ENTRY]


def exits() -> list[Point]:
    return [p for p in POINTS if p.direction == EXIT]
