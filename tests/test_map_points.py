"""The route map's data: the countries' borders and the positions of labels and points."""

import json

from core import map_points, points, tariffs
from core.tariffs import load_tariffs


def network():
    return points.build_network(points.build_catalog(load_tariffs(tariffs.DEFAULT_PATH).table))


def test_geojson_has_exactly_the_route_countries_and_is_small():
    data = json.loads(map_points.COUNTRIES_GEOJSON.read_text(encoding="utf-8"))
    codes = sorted(f["properties"]["code"] for f in data["features"])
    assert tuple(codes) == network().countries
    assert map_points.COUNTRIES_GEOJSON.stat().st_size < 300_000
    assert "Natural Earth" in data["source"]


def test_every_route_country_and_map_point_has_a_position():
    net = network()
    assert set(map_points.COUNTRY_LABELS) == set(net.countries)
    missing = [p.label for p in net.points if map_points.point_position(p.name, p.countries) is None]
    assert missing == []
    assert len(map_points.POINT_POSITIONS) == len(net.points)


def test_markers_are_not_on_top_of_each_other():
    positions = list(map_points.POINT_POSITIONS.values())
    for i, (x1, y1) in enumerate(positions):
        for x2, y2 in positions[i + 1:]:
            assert abs(x1 - x2) + abs(y1 - y2) >= 0.2, ((x1, y1), (x2, y2))
