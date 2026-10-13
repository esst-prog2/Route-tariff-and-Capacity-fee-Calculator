## Why

On the real tariffs, tab 1 shows a route as five tables: the network points, one product table per TSO and a summary per TSO, in three different currencies and units (HUF per kWh/h, EUR per kWh/h, EUR per kWh/d). A trader has to read all of them to see what each point costs, and the "saving" compares the cheapest plan with booking every day as a daily product, which nobody would do for a long period, so it overstates the benefit (BG to HU, 2026-10-01 to 2027-03-31: 2.3229 EUR/MWh against all daily, but only 0.2956 against the realistic alternative without quarters).

## What Changes

- **BREAKING - one table for the route.** The "Network points on the route" table keeps its columns (#, TSO, point, EIC, direction, capacity type) and gains two: **Products** and **EUR/MWh**. The per-TSO product tables and the "Summary per TSO" table are removed.
- **EUR/MWh per point.** Each point gets its own EUR/MWh figure, so the column adds up to the route total. Points of the same TSO still share one product choice; each point is costed with its own prices for those products (BG to HU: Gastrans entry Kireevo/Zaychar 0.8494 and exit Kiskundorozsma 2 0.9684, together the TSO's 1.8178).
- **Products per point.** The Products cell names the products the point books, as a trader books them (e.g. "Q4 2026, Q1 2027", "GY 2026/27", "Dec 2026 (+4 days), daily 01-15 Jan 2027"), and marks days booked outside the period. The over-booking note under the table stays.
- **BREAKING - the saving compares with the next shorter product.** The route total keeps the cheapest combination and the saving, but the comparison line is no longer "all daily". For each TSO it is the cheapest plan without the longest product type that TSO's cheapest plan uses (yearly -> without yearly, quarterly -> without quarterly, monthly -> daily only); the route figure is the sum over the TSOs. When every TSO's cheapest plan is daily only, there is no comparison and no saving line.
- **Details section.** The "Tariff used" information (which tariff row each point's product was priced from) moves to a collapsible "Details" section under the table.
- Unchanged: the optimiser and its product choice, the per-MWh formulas, the FX box, tab 2. The all-daily figures stay available in the core calculation (earlier tests keep them), but tab 1 no longer shows them.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `route-tariff-calculator`: the results panel becomes one point table with products and EUR/MWh per point plus the route total and a details section; cost per MWh is defined per point; the FX box's "no rate" behaviour refers to the new cells; a new requirement defines the next-shorter-product comparison and the saving.

## Impact

- Code: `core/route.py` (per-point cost and EUR/MWh, next-shorter comparison per TSO and for the route), `core/optimizer.py` (an option to leave out product types from the longest down, reusing the same rules), a product-label helper, `app.py` (tab 1 results rebuilt). Tab 2, `core/tariffs.py`, `core/points.py` and `core/fee.py` are not touched.
- Tests: new unit tests for the per-point split, the product labels and the comparison; tab 1 app tests rewritten for the new layout; existing optimiser, route and acceptance results (including the README sample figures and the all-daily figures in the core) stay unchanged.
- Docs: README section 1 (the tab 1 walk-through) is rewritten for the new layout with real-data figures; `PLANNING_LOG.md` already records the decisions (2026-10-13 entries).
