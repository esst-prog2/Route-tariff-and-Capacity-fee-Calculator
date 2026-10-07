## Context

See proposal.md for why. The current code is built around one TSO:

- `core/tariffs.py` keeps rows of one operator (`FGSZ`), one capacity type (`Firm`), one currency (HUF) and one unit (kWh/h), and `TariffTable` keys rows by **(EIC, direction)**. On the corridor that key collides: Gastrans and FGSZ both have EIC `21Z000000000505P` with Entry and Exit rows, and Gastrans and Bulgartransgaz both have `58Z-000000007-KZ` (both have an Entry row there, in opposite flows).
- `core/points.py` is a flat list of 12 FGSZ points.
- `core/route.py` has one `RouteOracle` that adds the entry and exit price and feeds one `optimize` call; all figures are HUF.
- `core/optimizer.py` is already generic: it asks a `PriceOracle` for day, month and quarter prices and never sees a currency or unit.
- `core/fee.py` divides kWh/d by 24 and rounds to whole HUF; `money.split_by_weights` splits a whole amount.

Facts about the data that shape the design (synthetic sample, `Capacity_fee` sheet): the operator codes are `FGSZ`, `Gastran` and `BGTRGAZ`; Bulgartransgaz switches from BGN to EUR rows on 2026-01-01; Gastrans' Interruptible rows next to Firm rows carry 0 for year, quarter and month (never used, because Firm wins), while the three points that fall back to Interruptible have full, non-zero prices.

## Goals / Non-Goals

**Goals:**
- One loader and one table for three TSOs, each in its own currency and unit, with the Firm-else-Interruptible rule per point.
- Corridor routes built from data (countries and borders), not hand-written per route.
- Reuse the optimiser unchanged, once per TSO.
- Keep tab 2's existing behaviour for FGSZ points byte-for-byte (same totals, same invoice).

**Non-Goals:**
- Other TSOs in the export (DESFA, GCA, ...) and routes beyond HU - RS - BG.
- Live FX, BGN conversion, yearly products on tab 1, within-day products.
- Renaming the `fgsz-network-points` capability (it now covers three TSOs; renaming would mean a remove-and-add of every requirement, done later if wanted).

## Decisions

**1. Points carry their TSO; the table key is (TSO, EIC, direction).**
`Point` gains a `tso` field (the source operator code) and a display name map (`Gastran` -> "Gastrans", `BGTRGAZ` -> "Bulgartransgaz"). `TariffTable` keys rows by `(operator, eic, direction)` and `Point.key` returns that triple. Alternative considered: keep (EIC, direction) and load each TSO into its own table. Rejected: the app and tests pass one table around, and the triple is the true identity the spec now states.

**2. Per-TSO currency and unit in one config table; BGN skipped as out of scope.**
`tariffs.py` gets a mapping `TSO_FORMATS = {"FGSZ": ("HUF", "kWh/h"), "Gastran": ("EUR", "kWh/h"), "BGTRGAZ": ("EUR", "kWh/d")}`. Rows are filtered in this order: operator in the map, direction Entry/Exit, then BGTRGAZ rows with currency BGN are dropped silently (scope), then the capacity-type rule, then per-row validation. Any other currency or unit mismatch is still an excluded-and-reported row, as today. Each `TariffRow` keeps its `currency`, `unit` and `capacity_type` so the UI never has to guess. Alternative: a generic "skip any currency other than the TSO's" rule. Rejected: it would also hide genuine data errors (e.g. an FGSZ row in EUR), which the spec still wants reported.

**3. Firm-else-Interruptible is decided per point after the currency filter.**
Group the in-scope rows by (operator, EIC, direction); if the group has any Firm row keep only Firm rows, else keep its Interruptible rows. Deciding after dropping BGN means a point whose only Firm rows were BGN would fall back to Interruptible; no corridor point is in that situation, and the alternative (deciding before) could leave a point with no usable rows at all. Never mixing the two types for one point keeps "capacity type" a property of the point, which is what both tabs show.

**4. Points and corridor topology live in `core/points.py` as data.**
`POINTS` becomes the 30-point table from the spec (each with tso, name, flow, eic, direction). A small structure describes the corridor:

```
COUNTRIES = ("HU", "RS", "BG")              # in corridor order
COUNTRY_TSO = {"HU": "FGSZ", "RS": "Gastran", "BG": "BGTRGAZ"}
BORDERS = {("HU","RS"): "21Z000000000505P", ("RS","BG"): "58Z-000000007-KZ"}

crossing(X, Y) -> [exit of COUNTRY_TSO[X] with flow X>Y at the border EIC,
                   entry of COUNTRY_TSO[Y] with flow X>Y at the border EIC]
route_points(A, B) -> crossings along the corridor from A to B, concatenated
```

The expected capacity type in the spec table is not stored on `Point`; it comes from the loaded rows (`TariffTable.capacity_type(point)`), so a real export with different Firm coverage is shown truthfully. Flow strings use the corridor codes, so "BG>RS" etc. are generated, not typed per route.

**5. One oracle per TSO; the optimiser is untouched.**
`route.py` replaces `RouteOracle(entry, exit)` with `TsoOracle(table, points)` that sums the prices of any number of points of one TSO (one for Bulgartransgaz and FGSZ on hub-to-hub routes, two for Gastrans when the route crosses Serbia). `calculate_route(table, begin, end_country, start, end, fx_text)` builds the route's points, groups them by TSO in route order, runs `optimize` once per TSO and returns a `RouteResult` holding a list of `TsoLeg(tso, points, plan, currency, unit)`. Per-MWh is a method on the leg: `plan.total / (hours_per_unit x days) x 1000` with `hours_per_unit` 24 for kWh/h and 1 for kWh/d. EUR/MWh per leg is that figure for EUR legs and figure / rate for HUF legs (None without a rate); the route totals are the sum of the legs' EUR/MWh, None if any leg's is None. Because each optimisation stays in one currency, the FX rate never reaches the optimiser (spec: "FX rate does not change the choice").
Alternative considered: one route-wide optimisation in EUR. Rejected by the user (2026-10-07): it ties the choice to the rate.

**6. Errors name TSO and point.**
`NoTariffError` takes the `Point` and formats "No tariff exists for Bulgartransgaz Kireevo/Zaychar (BG>RS) on 2025-12-01." The same-country check happens before any lookup. The old "same physical point" check and the entry/exit-direction check are removed with the old inputs.

**7. Tab 2: unit and currency per point; rounding in minor units.**
`fee.calculate_fee` reads the point's unit from its rows: kWh/h -> capacity / 24, kWh/d -> capacity as typed. Rounding generalises to "minor units": HUF has 0 decimals, EUR 2. The total is rounded to minor units (`round_whole(total x 10^d)`), `split_by_weights` is reused unchanged on that integer, and display divides back. FGSZ results therefore stay identical. `InvoiceLine.amount` and `FeeResult.total` become amounts in minor units plus a `currency` field; formatting moves to a `money.format_amount(minor, currency)` helper.

**8. UI.**
Tab 1: two selectboxes (HU/RS/BG, defaults BG -> HU), dates as now, the FX box rendered only when "HU" is the beginning or ending country. Results: point table, one segment table per TSO (column header names the unit, e.g. "EUR per kWh/d"), an over-booking note naming the TSO(s), an Interruptible note when any listed point is Interruptible, and the summary table described in the spec. Tab 2: TSO selectbox (display names) filters the point selectbox; metric labels take currency and unit from the result.

## Risks / Trade-offs

- [The real export may spell operators, EICs or units differently from the synthetic sample] -> The loader reports a clear message when a corridor point has no rows; task 9 has the user run the app against the real export locally before merging.
- [Bulgartransgaz has no EUR tariff before 2026-01-01, so many historical BG requests fail] -> Intended (user decision); the message names the TSO, point and date.
- [Interruptible prices are summed with Firm prices on HU->RS/BG routes as if equivalent] -> The point table shows the capacity type of each point and a note warns that Interruptible capacity can be interrupted; no discount or risk adjustment is modelled.
- [Grouping by TSO forces Gastrans' entry and exit onto one product even when splitting would be cheaper] -> Accepted (user decision, consistent with the 2026-09-25 FGSZ rule).
- [Tab 1 loses the FGSZ AT/SK/RO/HR/UA routes the demo and tests used] -> Intended (user decision); tests and README are rewritten around BG -> HU, and those points remain on tab 2.
- [The `fgsz-network-points` name no longer matches its content] -> Accepted for now; the main spec's Purpose sentence is updated at archive time.

## Migration Plan

No data migration: the sample already holds the new rows. `FGSZ_TARIFF_FILE` keeps its name so existing local setups keep working. The hosted Streamlit app redeploys from `main` after the merge; it still serves only the synthetic sample.
