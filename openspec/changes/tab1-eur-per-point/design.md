## Context

Tab 1 is built in `app.py` (`route_tab`) from a `RouteResult` (`core/route.py`): one `RouteLeg` per TSO, each holding the TSO's points and a `Plan` from `core/optimizer.py`. A leg's prices come from a `TsoOracle`, which sums the prices of the TSO's points, so a plan only knows the TSO's combined cost, not each point's share. `Plan` also carries `all_daily_total`, which tab 1 shows today as the comparison and which the existing acceptance tests (README sample figures) assert. See proposal.md for why the layout changes.

## Goals / Non-Goals

**Goals:**
- Per-point cost and EUR/MWh that add up exactly (as fractions) to the TSO's and the route's figures.
- A comparison plan per TSO that follows exactly the same optimisation rules as the cheapest plan, minus the excluded product types.
- Leave the optimiser's choice, tab 2 and all existing core results unchanged.

**Non-Goals:**
- No new optimiser behaviour for the cheapest plan (still one shared product choice per TSO).
- No per-point figures in the TSO's own currency on screen.

## Decisions

**1. Per-point cost from the chosen segments, not a second optimisation.** After a TSO's plan is chosen, each point's cost is the sum over the plan's segments of that point's own price for the segment's product (a `TsoOracle` over that single point, read at the segment's first day; daily segments sum the point's daily prices). Re-optimising each point alone was rejected: it could choose different products per point, breaking the "one product choice per TSO" rule and making the column disagree with the TSO's plan. The sum of the points' costs equals the plan total exactly, which a test asserts.

**2. Comparison plan by excluding product types in the optimiser.** `optimize` gets an optional parameter naming the longest product type allowed (default: yearly, i.e. today's behaviour). Rules 1-3 of the Optimization requirement stop at that level: with "monthly" no quarter or gas year is considered, with "daily" no month either. The comparison for a TSO is `optimize(..., longest=<the type below the cheapest plan's longest type>)`. Writing a separate "monthly-only" calculator was rejected because it would duplicate the over-booking and missing-tariff rules and could drift from them.

**3. Keep `all_daily_total` and the existing route totals.** They stay in `Plan`, `RouteLeg` and `RouteResult`, so the optimiser, route and acceptance tests (including the README sample figures 14.0247 / 5.8297) keep passing unchanged. Tab 1 simply stops showing them. New properties are added next to them for the comparison (per leg and per route, with the label data).

**4. Product labels as a pure function of a plan and the period.** A small function turns a plan's segments into the cell text (Product labels requirement), so it can be unit-tested without Streamlit. Points of one TSO share a plan, so they get the same text by construction.

**5. Details as a Streamlit expander.** `st.expander("Details", expanded=False)` with one table, rows per point and segment: TSO, point, dates, product, tariff used. The tariff used is taken per point (one `Valid from`), not the joined "entry ...; exit ..." text the per-TSO tables showed.

**6. Missing FX rate.** The FGSZ point's EUR/MWh cell is left blank (empty string) and the route total block is replaced by the existing prompt; the per-point EUR figures of the EUR TSOs are shown, as the FX box requirement says.

## Risks / Trade-offs

- [The point table gets wide on a phone (8 columns)] → Products text stays short (ranges for month runs); the EIC column can be the first to drop if it is too wide when checked by eye.
- [Comparison doubles the optimisation work per TSO] → The optimiser is linear in the days of the period; a second run per TSO is negligible.
- [Tab 1 app tests assert the old tables] → They are rewritten for the new layout in the same change; the core tests are not touched, which guards the numbers.
- [README section 1 describes the old layout] → Rewritten in the same change (see tasks).
