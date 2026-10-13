"""Where the route map draws things: the label position of each route country
and the position of each border point (longitude, latitude in degrees).

Typed in by hand from public locations; they only place labels and markers and
never affect a price. A few markers are set slightly apart from their true
place so that points close together stay clickable on the small map."""

from __future__ import annotations

from pathlib import Path

COUNTRIES_GEOJSON = Path(__file__).resolve().parent.parent / "data" / "map" / "countries.geojson"

# Country code (as in the tariff data) -> where its code is written.
COUNTRY_LABELS: dict[str, tuple[float, float]] = {
    "AT": (14.3, 47.55),
    "BG": (25.2, 42.75),
    "CR": (16.3, 45.45),
    "CZ": (15.3, 49.85),
    "DE": (10.3, 51.2),
    "GR": (22.0, 39.6),
    "HU": (19.3, 47.15),
    "IT": (12.6, 43.1),
    "NL": (5.7, 52.3),
    "PL": (19.3, 52.1),
    "RO": (24.8, 45.9),
    "RS": (20.8, 44.1),
    "SI": (14.7, 46.1),
    "SK": (19.4, 48.75),
    "UA": (25.6, 49.3),  # in western Ukraine: the map is cut east of the border points
}

# (point name, the two countries in alphabetical order) -> marker position.
POINT_POSITIONS: dict[tuple[str, tuple[str, str]], tuple[float, float]] = {
    ("Baumgarten", ("AT", "SK")): (16.8, 48.42),  # nudged north-west, away from Mosonmagyaróvár
    ("Mosonmagyaróvár", ("AT", "HU")): (17.2, 47.85),  # nudged south-east
    ("VIP Oberkappel", ("AT", "DE")): (13.78, 48.56),
    ("Tarvisio/Arnoldstein", ("AT", "IT")): (13.6, 46.55),
    ("Murfeld/Ceršak", ("AT", "SI")): (15.67, 46.7),
    ("Kulata/Sidirokastron", ("BG", "GR")): (23.37, 41.4),
    ("Negru Voda 1/Kardam", ("BG", "RO")): (28.15, 43.79),
    ("Ruse/Giurgiu", ("BG", "RO")): (25.97, 43.87),
    ("Kireevo/Zaychar", ("BG", "RS")): (22.66, 43.9),
    ("Drávaszerdahely", ("CR", "HU")): (17.8, 45.83),
    ("Rogatec", ("CR", "SI")): (15.7, 46.23),
    ("VIP Brandov-GASPOOL", ("CZ", "DE")): (13.4, 50.63),
    ("Cieszyn", ("CZ", "PL")): (18.63, 49.75),
    ("Lanžhot", ("CZ", "SK")): (16.97, 48.8),  # nudged north, away from Baumgarten
    ("VIP TTF-THE-H", ("DE", "NL")): (7.2, 53.23),
    ("Csanádpalota", ("HU", "RO")): (20.75, 46.25),
    ("Kiskundorozsma 2", ("HU", "RS")): (19.95, 46.17),
    ("Balassagyarmat", ("HU", "SK")): (19.3, 48.08),
    ("VIP Bereg", ("HU", "UA")): (22.53, 48.2),
    ("Gorizia/Šempeter", ("IT", "SI")): (13.64, 45.92),
    ("Vyrava", ("PL", "SK")): (21.97, 49.3),
    ("Uzhgorod/Velké Kapušany", ("SK", "UA")): (22.13, 48.55),
}


def point_position(name: str, countries: tuple[str, str]) -> tuple[float, float] | None:
    return POINT_POSITIONS.get((name, countries))


FRAME_MARGIN = 0.8  # degrees around the outermost point or label


def map_frame() -> dict:
    """The area the map is zoomed to: the box around every border point and country label, as
    GeoJSON for the projection's fit."""
    xs = [x for x, _ in [*POINT_POSITIONS.values(), *COUNTRY_LABELS.values()]]
    ys = [y for _, y in [*POINT_POSITIONS.values(), *COUNTRY_LABELS.values()]]
    west, east = min(xs) - FRAME_MARGIN, max(xs) + FRAME_MARGIN
    south, north = min(ys) - FRAME_MARGIN, max(ys) + FRAME_MARGIN
    return {"type": "Feature", "properties": {},
            "geometry": {"type": "MultiPoint", "coordinates": [[west, south], [east, north]]}}
