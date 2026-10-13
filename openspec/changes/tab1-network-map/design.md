## Context

See proposal.md for motivation. Today `core/points.py` hard-codes the HU - RS - BG corridor (`COUNTRIES`, `COUNTRY_TSO`, `BORDER_EICS`, `route_points(begin, end)`), and `core/route.py`'s `calculate_route(table, begin, end, start, end, fx_rate_text)` groups the corridor's points by TSO, optimises each TSO and converts only FGSZ with one HUF rate. The point catalog built from the tariff rows (`build_catalog`) already has every single side with its name, flow, EIC and capacity type, and pairs bundles by EIC and flow (plus Baumgarten). On the real file the exit/entry pairs give 47 directed crossings at 25 places; 22 of them connect the 15 route countries. Streamlit 1.64 ships Altair 6, whose charts can report selections back to the app (`st.altair_chart(..., on_select="rerun")`).

## Goals / Non-Goals

**Goals:**
- Build the network from the catalog, so the map and the route checks follow the tariff data.
- Keep the optimiser, the per-point costs, the comparison and the Details exactly as they are; only how the route's points are found and how rates are applied changes.
- Make every route reachable without the map (the "Next point" dropdown), so tab 1 can be tested headlessly.

**Non-Goals:**
- Searching or ranking paths (user decision).
- Routes through TAP or ICGB, LNG terminals or one-sided border points.
- A detailed map (rivers, cities, tiles) or geographic accuracy beyond placing each point on its border.

## Decisions

### 1. Network derived from the catalog
`core/points.py` gains `build_network(catalog) -> Network`. A crossing is an (exit, entry) pair of two TSOs with the same flow and either the same EIC or the Baumgarten pair (`EXTRA_BUNDLES`), using every single side whatever its capacity type, so Interruptible-only crossings (HU>RS, HU>AT, SI>AT, RS>BG) stay routable. A `MapPoint` groups the crossings of one place: its cleaned name and the unordered pair of countries; it knows its crossing for each direction. Route countries are the countries that are both entered and left at some map point; points touching a non-route country (TAP, ICGB) are dropped, which removes Stara Zagora, Komotini and Nea Mesimvria. The corridor constants and `route_points`/`crossing` are removed; the curated `POINTS` names stay.

*Alternative:* a hand-written list of the 22 points and their crossings. Rejected: it would drift from the tariff data, which the catalog already reads.

### 2. Route = beginning country + ordered map points, checked one step at a time
A pure function `extend_route(network, begin, points, new_point) -> list | RouteError` adds one point or returns the message (does not border the current country; enters a country already on the route). `route_crossings(network, begin, points)` turns a valid route into its ordered exit/entry `Point`s, which `calculate_route` then groups by TSO as today. `calculate_route` takes `begin`, the point ids and a mapping currency -> rate text instead of `begin`, `end_country` and one FX text.

### 3. Rates per currency
`TsoLeg.fx_rate` becomes the rate of the leg's own currency (None for EUR or when missing/invalid). `RouteResult` keeps the parsed rates and the currencies still needed, so the app can show one box per non-EUR currency, the prompt naming the missing ones, and "at 1 EUR = X HUF; at 1 EUR = Y RON". Parsing reuses `parse_fx_rate` per currency. A leg's EUR figures are None until its rate is known; the route total is None until every leg has one, as today for FGSZ.

### 4. The map in Altair
One layered Altair chart, 750 px high, Mercator projection fitted to the box around the border points and country labels (not to the 15 countries, which would shrink the map to fit eastern Ukraine; added after the user found the points too close together), with the borders cut at the frame:
- `mark_geoshape` of the countries from a committed GeoJSON (`data/map/countries.geojson`: Natural Earth 1:50m admin-0, public domain, cut to the 15 countries and simplified to keep the file small), no fill colour, thin grey borders;
- `mark_text` of each country code at a hand-set label position (not the polygon centroid, which can fall outside or on a border);
- `mark_circle` markers at the points' coordinates with a point selection on click and a tooltip "name (country - country)"; markers on the route are highlighted, and a `mark_line` joins them in route order.

Point coordinates live in a small table in `core/map_points.py`, keyed by (cleaned name, country pair), typed in by hand from public locations and checked by the user. Markers closer than a few kilometres on screen (Kiskundorozsma 2 / Csanádpalota, Baumgarten / Mosonmagyaróvár) get a small offset there. A test asserts that every map point of the real file has coordinates; a point without coordinates would still be offered by the "Next point" dropdown.

*Alternatives:* Plotly (installed locally but not a project dependency, and choropleth click events are less certain in Streamlit) and `streamlit-folium` (new dependency, tile-based map, not minimal). Altair needs nothing new.

### 5. Route state and clicks
The route's points live in `st.session_state` (default: Kireevo/Zaychar, Kiskundorozsma 2 with beginning BG). A map click arrives as the chart's selection on the next rerun; the app compares it with the last click it processed, adds the point through `extend_route`, and gives the chart a new key after each change so the selection starts empty again (otherwise the same selection would be re-added on every rerun). The "Next point" dropdown, "Remove last" and "Clear" change the same state. Changing the beginning clears the points. Messages from a refused point are shown once, above the map.

The spike (task 1) confirms in this Streamlit version that a click on a `mark_circle` with a point selection arrives in `on_select="rerun"` with the point's id, and that changing the key clears it. If it does not, the fallback is a Plotly scattergeo map with Streamlit's plotly selection events, keeping everything else.

### 6. Country codes as in the tariff data
The map and the route text use the flow codes of the data (CR for Croatia, not HR), so the route text matches the point flows shown in the point table.

## Risks / Trade-offs

- [Map clicks behave differently than expected in Streamlit] -> Spike first (decision 5), fallback to Plotly; the dropdown works regardless.
- [Hand-typed coordinates are wrong] -> The user checks them on the map (task); they only place markers and never affect prices.
- [A new tariff file adds a border point] -> It appears in the network and the dropdown automatically; the coordinates test fails until its position is added.
- [The route state is lost on a page reload] -> Acceptable; the default route is restored.

## Migration Plan

Implement on a git branch named after the change. Tab 1's tests that call `calculate_route(table, begin, end, ...)` move to the beginning-plus-points form; their figures stay, since the default route equals the old BG to HU route. The README's tab 1 walk-through is rewritten for the map with the same figures. Rollback is reverting the merge commit.
