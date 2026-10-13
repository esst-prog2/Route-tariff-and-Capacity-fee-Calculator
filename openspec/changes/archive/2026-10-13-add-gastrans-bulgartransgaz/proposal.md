## Why

The MVP covers only FGSZ, but the trades the department prices most often run along the HU - RS - BG corridor, through Gastrans (Serbia) and Bulgartransgaz (Bulgaria). A trader wants to pick where the gas starts and where it ends (Hungary, Serbia or Bulgaria) and see every network point on the way with its cost, instead of pricing each TSO by hand. Both TSOs are already in the tariff export (`Gastran`, `BGTRGAZ`), with their own currency (EUR) and, for Bulgartransgaz, their own capacity unit (kWh/d).

## What Changes

- **Two more TSOs.** Gastrans (EUR per kWh/h) and Bulgartransgaz (EUR per kWh/d) are loaded alongside FGSZ (HUF per kWh/h). Each Bulgartransgaz price cell is the price of 1 kWh/d for the whole product period (cost for C kWh/d = C x cell). Bulgartransgaz's earlier BGN rows are skipped silently as out of scope, so its points have no tariff before 2026-01-01.
- **Interruptible where Firm is missing.** A point that has no Firm rows uses its Interruptible rows. On the corridor that is FGSZ exit Kiskundorozsma 2 (HU>RS), Gastrans entry Kiskundorozsma 2 (HU>RS) and Gastrans exit Kireevo/Zaychar (RS>BG). Points with Firm rows keep using Firm only.
- **BREAKING - tab 1 becomes a corridor route calculator.** The TSO, entry and exit dropdowns are replaced by "Route beginning" and "Route ending" (HU, RS, BG). A route is hub to hub: it books the exit and the matching entry at every border it crosses (BG->HU = 4 points, HU->RS = 2 points). A route that begins and ends in the same country is not possible. The FGSZ-only entry-to-exit routes (e.g. Mosonmagyaróvár AT>HU to Kiskundorozsma HU>RS) are dropped.
- **Optimiser per TSO.** Points of the same TSO on a route use the same product; each TSO is optimised separately in its own currency and unit, so the choice never depends on the FX rate. The over-booking rules are unchanged.
- **New tab 1 results.** A list of every network point on the route (TSO, point, EIC, direction, capacity type); the chosen products per TSO in its own currency and unit; a summary per TSO and for the route, where the route total, the all-daily baseline and the saving are given in EUR/MWh only. The FX box appears only when the route touches HU.
- **Tab 2 gets three TSOs.** The TSO dropdown offers FGSZ, Gastrans and Bulgartransgaz and the point list follows it (FGSZ 13 points, Gastrans 4, Bulgartransgaz 13). Costs stay in the point's own currency and unit; EUR is rounded to cents, HUF to whole forints, and the monthly invoice still adds up exactly to the total.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `tariff-loading`: scope widens to three TSOs with a Firm-else-Interruptible rule per point; each TSO has its own expected currency and unit; Bulgartransgaz's BGN rows are skipped silently; the price-cell meaning covers kWh/d; rows are told apart by TSO as well as EIC and direction.
- `fgsz-network-points`: the supported points become the three TSOs' lists plus the HU - RS - BG corridor topology; labels mark Interruptible points; the TSO dropdown stays on tab 2 only. (The capability keeps its existing name.)
- `route-tariff-calculator`: route inputs, route validity, route price, optimisation grouping, results panel, cost per MWh and the FX box are rewritten for hub-to-hub corridor routes.
- `capacity-fee-calculator`: inputs, fee calculation, monthly invoice rounding and currency handle EUR and kWh/d points as well as HUF.

## Impact

- Code: `core/tariffs.py` (scope, currency and unit per TSO, table key), `core/points.py` (three TSOs, countries and borders), `core/route.py` (hub-to-hub routes, one oracle per TSO, EUR/MWh totals), `core/fee.py` and `core/money.py` (native unit and currency, rounding to cents), `app.py` (tab 1 rebuilt, tab 2 TSO filter). `core/optimizer.py` is reused unchanged.
- Tests: tariff, point, route, fee, app and acceptance tests updated; the acceptance tests and the README demo move from Mosonmagyaróvár -> Kiskundorozsma to a corridor route.
- Docs: README (demo, shape, scope); `PLANNING_LOG.md` records the decisions (2026-10-07 entries).
- Data: no new file; the synthetic sample already contains the Gastrans and Bulgartransgaz rows. The real export must be checked locally to make sure it uses the same operator codes and EICs.
