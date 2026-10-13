## 1. Branch and spike

- [x] 1.1 Create the git branch `tab1-network-map` from `main` and verify `python -m pytest -q` passes before any change
- [x] 1.2 Spike (throwaway script outside the app): an Altair map with clickable `mark_circle` markers in `st.altair_chart(on_select="rerun")`; verify by hand in the browser that a click returns the marker's id and that a new chart key clears the selection, and record the result (or switch the design to the Plotly fallback) before task 4

## 2. Network topology

- [x] 2.1 Add `build_network` (crossings, map points, route countries) to `core/points.py`; verify on the real file: 22 map points with the names of the "Map points on the real file" scenario, 15 route countries, and the "Crossing at a point with two TSOs in one country" and "Points without a partner are not map points" scenarios
- [x] 2.2 Add `extend_route` and `route_crossings`; verify the "Route points" scenarios (BG to HU, RS to HU, HU to BG, RS to BG, through Romania, two TSOs in one country) and the "Route validity" scenarios (same country, point not on the current country) in tests
- [x] 2.3 Remove the corridor constants, `route_points` and `crossing`, and move their callers to the network; verify the existing route, points and acceptance tests pass after rewriting their routes as beginning plus points (same figures)

## 3. Route calculation and rates

- [x] 3.1 Change `calculate_route` to take the beginning country, the point ids and a rate per currency, with each leg converted by its own currency's rate; verify the "FX rate box" scenarios (route without HU, no rate, rate entered, invalid rate, several currencies, all-EUR route) and "A point in RON" in tests
- [x] 3.2 Verify on the real file that BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU, 2026-10-01 to 2027-03-31 at 400 HUF/EUR still gives 1.4431, 0.8494, 0.9684, 0.4348 and 3.6957 EUR/MWh

## 4. Map data

- [x] 4.1 Add `data/map/countries.geojson` with the 15 countries' borders (Natural Earth 1:50m admin-0, public domain, cut and simplified) and note its source and licence in the README; verify the file has exactly those 15 countries and stays under 300 KB
- [x] 4.2 Add `core/map_points.py` with the label position of each country and the coordinates of the 22 map points (small offsets for markers that sit close together); verify with a test that every map point of the real file and every route country has a position

## 5. Tab 1 UI

- [x] 5.1 Replace the route dropdowns with "Route beginning", the Altair map, the "Next point" dropdown, the route text and the "Remove last" and "Clear" buttons, with the route in session state and the default route on opening; verify with AppTest through the "Next point" dropdown and buttons ("Next point follows the route", "Remove last and clear", "Changing the beginning clears the route", "No point yet")
- [x] 5.2 Handle map clicks as in design decision 5 and show refused points' messages; verify by hand in the browser (adding, refusing Vyrava from BG, refusing a second entry into HU)
- [x] 5.3 Show one rate box per non-EUR currency on the route, the prompt for missing rates and the rates used; verify with AppTest on the real file for BG > Ruse/Giurgiu > RO > Csanádpalota > HU and AT > Tarvisio/Arnoldstein > IT

## 6. Docs and check

- [x] 6.1 Rewrite the README's tab 1 walk-through for the map (default route figures unchanged; one route through Romania); verify every figure quoted matches the app
- [x] 6.2 Run the full test suite and verify it passes
- [x] 6.3 User checks the map by eye: the borders, country codes and point positions, clicking a route BG > RO > HU and HU > SK > PL, and a refused click
