"""Draw the promo page's map (docs/index.html) from the app's own map data.

Countries come from data/map/countries.geojson (Natural Earth 1:50m, public domain), border points
from core/map_points.py, the same data the app's route map uses. The route lit on the page is the
README example, BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU, with each point's EUR/MWh from a
real run (asserted in tests/test_route.py). The SVG is written between the map markers in
docs/index.html, so the page needs no build step. Run: python tools/build_map_svg.py
"""

from __future__ import annotations

import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import map_points  # noqa: E402

PAGE = ROOT / "docs" / "index.html"
WIDTH = 1000  # viewBox width; the height follows the frame's Mercator aspect

# The lit route: each border point with its two operators and their EUR/MWh (README demo, tests).
ROUTE = [
    (("Kireevo/Zaychar", ("BG", "RS")), [("1", "Bulgartransgaz exit", "1.4431"), ("2", "Gastrans entry", "0.8494")]),
    (("Kiskundorozsma 2", ("HU", "RS")), [("3", "Gastrans exit", "0.9684"), ("4", "FGSZ entry", "0.4348")]),
]
ROUTE_COUNTRIES = {"BG", "RS", "HU"}


def merc_y(lat: float) -> float:
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def build() -> str:
    (west, south), (east, north) = map_points.map_frame()["geometry"]["coordinates"]
    x_scale = WIDTH / math.radians(east - west)
    height = round(x_scale * (merc_y(north) - merc_y(south)))

    def xy(lon: float, lat: float) -> tuple[float, float]:
        return (round(math.radians(lon - west) * x_scale, 1), round((merc_y(north) - merc_y(lat)) * x_scale, 1))

    geo = json.loads((ROOT / "data" / "map" / "countries.geojson").read_text(encoding="utf-8"))
    countries = []
    for feature in geo["features"]:
        code = feature["properties"]["code"]
        parts = []
        for polygon in feature["geometry"]["coordinates"]:
            for ring in polygon:
                pts = [xy(lon, lat) for lon, lat in ring]
                parts.append("M" + "L".join(f"{x:g} {y:g}" for x, y in pts) + "Z")
        cls = "c route-c" if code in ROUTE_COUNTRIES else "c"
        countries.append(f'<path class="{cls}" d="{"".join(parts)}"><title>{html.escape(feature["properties"]["name"])}</title></path>')

    labels = []
    for code, (lon, lat) in map_points.COUNTRY_LABELS.items():
        x, y = xy(lon, lat)
        cls = f"cc cc-{code.lower()}" + (" route-cc" if code in ROUTE_COUNTRIES else "")
        labels.append(f'<text class="{cls}" x="{x:g}" y="{y:g}">{code}</text>')

    route_keys = {key for key, _ in ROUTE}
    points = []
    for (name, pair), (lon, lat) in map_points.POINT_POSITIONS.items():
        if (name, pair) in route_keys:
            continue
        x, y = xy(lon, lat)
        label = html.escape(f"{name} ({pair[0]}–{pair[1]})")
        points.append(f'<g class="pt" tabindex="0" aria-label="{label}"><circle cx="{x:g}" cy="{y:g}" r="5"/>'
                      f'<text x="{x + 9:g}" y="{y + 4:g}">{html.escape(name)}</text></g>')

    (a_lon, a_lat), (b_lon, b_lat) = (map_points.POINT_POSITIONS[k] for k, _ in ROUTE)
    ax, ay = xy(a_lon, a_lat)
    bx, by = xy(b_lon, b_lat)
    route = [f'<path class="route-line" d="M{ax:g} {ay:g}L{bx:g} {by:g}" pathLength="1"/>']
    # Callouts to the right of each point: Kireevo/Zaychar below its point, Kiskundorozsma 2 above.
    for i, (((name, _pair), ops), (px, py), (dx, dy, anchor)) in enumerate(zip(
            ROUTE, [(ax, ay), (bx, by)], [(46, 64, "start"), (52, -58, "start")])):
        tx, ty = px + dx, py + dy
        rows = "".join(
            f'<tspan x="{tx:g}" dy="{18 if j else 0}"><tspan class="n">{n}</tspan> {html.escape(op)} '
            f'<tspan class="v">{v}</tspan></tspan>' for j, (n, op, v) in enumerate(ops))
        route.append(
            f'<g class="rp rp{i + 1}" tabindex="0" aria-label="{html.escape(name)}: '
            f'{", ".join(f"{op} {v} EUR/MWh" for _n, op, v in ops)}">'
            f'<path class="lead" d="M{px:g} {py:g}L{tx - (6 if anchor == "start" else -6):g} {ty - 22:g}"/>'
            f'<circle cx="{px:g}" cy="{py:g}" r="7"/>'
            f'<text class="rp-name" x="{tx:g}" y="{ty - 22:g}" text-anchor="{anchor}">{html.escape(name)}</text>'
            f'<text class="rp-ops" x="{tx:g}" y="{ty:g}" text-anchor="{anchor}">{rows}</text></g>')

    return (f'<svg class="map-svg" viewBox="0 0 {WIDTH} {height}" preserveAspectRatio="xMidYMid slice" '
            f'role="img" aria-labelledby="map-title">'
            f'<title id="map-title">Map of the 15 countries and 22 border points the calculator covers, with the '
            f'route BG to RS to HU lit and priced point by point</title>'
            f'<rect class="sea" width="{WIDTH}" height="{height}"/>'
            f'<g class="countries">{"".join(countries)}</g><g class="labels">{"".join(labels)}</g>'
            f'<g class="points">{"".join(points)}</g><g class="route">{"".join(route)}</g></svg>')


def main() -> None:
    page = PAGE.read_text(encoding="utf-8")
    new, count = re.subn(r"(<!-- map:start -->).*?(<!-- map:end -->)",
                         lambda m: m.group(1) + build() + m.group(2), page, flags=re.S)
    if count != 1:
        raise SystemExit("docs/index.html needs exactly one <!-- map:start --> ... <!-- map:end --> block")
    PAGE.write_text(new, encoding="utf-8")
    print(f"map written into {PAGE.relative_to(ROOT)} ({len(build()) // 1024} KB)")


if __name__ == "__main__":
    main()
