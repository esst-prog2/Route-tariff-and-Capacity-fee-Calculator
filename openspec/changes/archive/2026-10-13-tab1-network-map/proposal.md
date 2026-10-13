## Why

The Route Tariff Calculator still prices routes only along the HU - RS - BG corridor, while the app now knows 21 TSOs whose border points connect 15 countries. Traders usually know which way they want to send the gas (for example BG - RS - HU or BG - RO - HU, HU - SK - PL), so tab 1 should let them pick the exact border points of a route anywhere in that network and then optimise each TSO's products for the booking period, as it already does on the corridor. Finding the cheapest path is not needed.

## What Changes

- **BREAKING** Tab 1's "Route ending" dropdown and the fixed corridor go away. A route is chosen with a "Route beginning" dropdown (15 countries) and a minimal interactive map that draws only the borders of those countries, with each country's code in its middle and a marker on each of the 22 border points between them. Clicking markers in order adds the points to the route; a "Next point" dropdown does the same by keyboard. The route is shown as text ("BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU") with "Remove last" and "Clear" buttons.
- A clicked point that does not border the country the route has reached, or that would enter a country already on the route, is not added, and a message says the route is not possible and why.
- The route is hub to hub along the chosen points: at each point the exit of the TSO of the country the gas leaves and the entry of the TSO of the country it enters, in the direction of travel (Firm, or Interruptible where a side has no Firm). Where a country has several TSOs (Austria: Gas Connect Austria and Trans Austria Gasleitung; Germany: Open Grid Europe, GASCADE and Gasunie Deutschland), each border point uses the TSO that operates it.
- The single HUF rate box becomes one rate box per non-EUR currency on the route (HUF, RON, CZK or PLN per 1 EUR). Each point's EUR/MWh appears once its currency has a rate, and the route total once every rate is typed.
- Unchanged: the per-TSO product optimiser, the point table with products and EUR/MWh, the comparison with the next shorter products, the Details section, over-booking and part-by-part pricing across tariff changes.
- Tab 1 opens on today's default route, BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `route-tariff-calculator`: route inputs (beginning country, map, next-point dropdown, route text and buttons), route points along the chosen border points, route validity messages for impossible selections, one rate box per non-EUR currency, cost per MWh in any currency, and a new requirement for the route map.
- `fgsz-network-points`: the fixed HU - RS - BG corridor is replaced by a network topology built from the point catalog (countries, border crossings, the 22 map points); the TSOs on a route follow from its points.

## Impact

- Code: `core/points.py` (network topology instead of the corridor), `core/route.py` (route from a beginning country and a list of border points; rates per currency), `app.py` (map, next-point dropdown, route state, rate boxes), a new module for the map's point coordinates.
- Data: a small committed GeoJSON file with the 15 countries' borders (Natural Earth, public domain) and a hand-made table of the 22 points' coordinates.
- Dependencies: none new (Altair ships with Streamlit); a spike checks that Streamlit reports clicks on Altair map markers.
- Tests: tab 1 tests are rewritten around beginning country plus points; the README demo, the acceptance tests and the route scenarios that name "BG to HU" keep their figures, since the default route is the same.
