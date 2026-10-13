## Context

See proposal.md for motivation. Today `core/tariffs.py` hard-codes three TSOs in `TSO_FORMATS`, the default file is the synthetic sample, and `core/points.py` holds a hand-written table of 30 points plus the HU - RS - BG corridor that tab 1 uses. `core/fee.py` prices one point and returns one `FeeResult`; `core/money.py` knows minor units only for HUF (0 decimals) and EUR (2).

The real file has 749 rows. After the scope filter (21 TSOs, Entry/Exit, Firm or Interruptible, no BGN/HRK rows) it gives 123 points. Pairing exits and entries by EIC gives 41 Firm+Firm bundles; Baumgarten adds 2 by hand. Source `Network point` names are inconsistent: most carry a country suffix and a parenthesised flow ("Csanádpalota - RO (RO>HU)"), some carry the flow without parentheses ("Kipoi TR>TAP", "Rogatec CRO -> SI"), a few have no flow at all ("Mazara del Vallo", "Klaipeda – LNG"), and some have extra words ("virtual", "virtuális", "(FSRU)", ", WAG").

## Goals / Non-Goals

**Goals:**
- One catalog of single sides, LNG entries and bundles, built from the loaded rows, so a new tariff row for an existing point needs no code change.
- Tab 2 prices a bundle as two independent sides; the existing single-point pricing is reused per side, unchanged.
- Tab 1 keeps working unchanged on the corridor, now on the real file.

**Non-Goals:**
- Routing across the whole network on tab 1 (change (b)).
- Live FX rates; the rates are typed by the user as on tab 1.
- New TSOs appearing in a future file without a code change: a TSO still needs its currency, unit and display name configured.

## Decisions

### 1. TSO configuration in one table
`TSO_FORMATS` grows to 21 entries (currency, unit) and gains the display name, so the scope filter, the currency check and the names come from one table. Scope is an allow-list of these 21 codes, not a deny-list of the 8 excluded operators: any operator not configured has an unknown currency and unit, so it cannot be priced anyway. `SKIPPED_CURRENCIES` gains `plinacr: ("HRK",)`. Capacity types other than Firm and Interruptible are dropped before the Firm-else-Interruptible choice, so GASCADE's DZK rows never count as "the point has rows".

*Alternative:* deny-list the 8 operators. Rejected: a new operator in the file would then reach the loader with no currency rule and be reported row by row as an error.

### 2. Catalog derived from the rows, with an override table
`core/points.py` builds the catalog from `TariffTable.keys()` (TSO, EIC, direction) after loading, instead of the fixed `POINTS` tuple:
- **Exclusions** are a set of (TSO, EIC) pairs: FGSZ 21W000000000087M, 39WKETELJCS57EN5, 39WKEMEHKER1NNNV, 39ZSZOREG1--FGTZ, TSO_EXIT_SUM_HU; Bulgartransgaz 21W000000000031C; Eustream 21Y000000000102O; Gas Connect Austria 21Z0000000000600; Trans Austria Gasleitung 21Z000000000164P.
- **Name and flow** come from a cleaning rule: take the flow from the last parenthesised "X>Y" (ignoring a trailing ", WAG"/", TAG"/", GCA"), else from a bare "X>Y" or "X -> Y" in the text; the name is what precedes it, with a trailing " - XX" or " XX" country code, "(FSRU)", "virtual"/"virtuális" and a trailing ", LNG-Zone" removed. Points the rule cannot clean are listed in an override table keyed by (TSO, EIC, direction) that gives the name and flow directly (at least Mazara del Vallo with flow LY>IT, Klaipeda, the Negru Voda 1/Kardam and Cieszyn names, and the existing FGSZ cleanups such as "Beregdaróc" without "1400" and "Balassagyarmat" without "/Velké Zlievce" and "MGT"). The cleaned names of the current 30 points stay as they are.
- **LNG entries** are entries whose flow starts with "LNG>", plus the Klaipeda entry via the override table.
- **Bundles** pair each exit with every entry of another TSO that has the same EIC and the same flow, keeping only Firm+Firm pairs, plus the Baumgarten pairs from the override table (Eustream 21Y---A001A023-Y with Gas Connect Austria 21Z000000000163R). A bundle's name is the entry side's cleaned name.

A test asserts the counts on the real file (109 single sides, 14 LNG entries, 43 bundles) and lists every cleaned name, so any change in the cleaning rule is visible in review.

*Alternative:* extend the hand-written table to about 170 rows. Rejected (user decision): the table would have to be kept in step with every new file by hand.

### 3. Point keeps its shape; Bundle is a new pair type
`Point` keeps (tso, name, flow, eic, direction), so the corridor code of tab 1 and its `key` lookup are untouched. The corridor's `_point` helper looks points up in the derived catalog instead of the old tuple. A new `Bundle(exit: Point, entry: Point)` carries the label and the year-list start (the later of the two sides' earliest `Valid from`). A `kind` (single side or LNG entry) is kept next to each point in the catalog, not on `Point` itself.

### 4. Bundled fee = two single-point fees
`calculate_fee` stays the single-point calculation and is called once per side; a new `calculate_bundle_fee` returns both `FeeResult`s, or the first `FeeError`, reworded to name the side ("No tariff exists for the FGSZ entry side ..."). The EUR total is a separate function taking the two results and a mapping currency -> typed rate; it returns either the total in EUR cents with the rates used, or the list of missing or invalid rates. It works on the rounded side totals, so the total matches the figures on screen. The FX parsing reuses `parse_number` (thousands and decimal commas) as on tab 1.

### 5. Minor units per currency
`CURRENCY_DECIMALS` becomes {HUF: 0, EUR: 2, RON: 2, CZK: 2, PLN: 2}. Rounding and the invoice split already work on minor units, so nothing else changes.

### 6. Default file
`resolve_tariff_path` falls back to `data/real/tariffs_real.xlsx` (`DEFAULT_PATH`). `DEFAULT_SAMPLE_PATH` stays as a name for the tests. A pytest fixture in `tests/conftest.py` sets `FGSZ_TARIFF_FILE` to the sample for the app tests, so the existing tests keep their sample-based figures; tests of the new behaviour load the real file explicitly.

### 7. Tab 2 layout
A horizontal radio "Booking type" (Bundled / Single side / LNG entry) comes first; each type has its own selectbox key, so switching the type never keeps a point of the wrong kind, as with the per-TSO widgets today. For a bundle the result shows two blocks, exit side first, each with the existing per-point layout (capacity, price cell, tariff used, total, invoice table), then the rate boxes, and then the EUR total or the missing-rate message. Default selection: Bundled, Mosonmagyaróvár AT>HU, 2026 Q4.

### 8. Products priced part by part across tariff changes
Added after the first implementation (user request): most new TSOs change their tariffs on 1 January, so pricing a gas year from the row valid on 1 October ignored the next calendar year's tariff. One function on `TariffTable`, `product_parts(point key, first, last)`, splits the product period where the applicable row changes and returns (first, last, row) parts; it raises a no-row error naming the first uncovered day. The split points are the rows' `Valid from` dates and the day after their `Valid to` dates inside the period, so a year costs a handful of lookups, not 365. A product price is Σ cell(row) x part days / product days, with the cell chosen by the product (`Year`, `Q*`, `M_*`).
- Tab 2: `FeeResult` keeps `price` as the weighted product price and gains `parts` (dates, days, row, cell), so the "Price" metric can show every cell (e.g. "3.9700 / 4.1000") and the caption lists each row with its dates. Each month's invoice weight is that month's exact cost under the parts, passed to the existing largest-remainder split (`split_by_weights` already takes exact fractions; all-zero weights fall back to days).
- Tab 1: `TsoOracle` prices yearly, quarterly and monthly products through the same function, so the optimiser, the point costs and the comparison plan all follow it; `tariff_used` and the Details "Tariff" column cover the whole product period instead of its first day. The optimiser's "not an option" rule for a product starting before the period now applies when any of its days has no row.

*Alternative:* twelfths of the yearly cell per month. Rejected (user decision): splitting by days matches the invoice split and handles changes inside a month or quarter (Eustream 1 May, Plinovodi 2 January).

## Risks / Trade-offs

- [The cleaning rule mis-names a point in a future file] → The name test on the real file lists every cleaned name; the override table fixes single cases without touching the rule.
- [Two sides of a border spelled differently, e.g. "Murfeld/Cersak" and "Murfeld/Ceršak"] → The bundle uses the entry side's name only; the override table can align the single sides if needed.
- [Tariff years differ between sides: many TSOs change tariffs on 1 January] → Each side is priced part by part from its own rows (decision 8), so a bundle's two sides may split the same gas year at different dates.
- [Tab 1 figures move where a corridor product crosses a tariff change] → The corridor TSOs change tariffs on 1 October (Bulgartransgaz also on 1 January); tests and README figures are re-checked after the change.
- [The hosted app and the default local run now show real tariffs] → The data is public (2026-10-13 log entry); the README says so.
- [Existing app tests silently switch to the real file] → The conftest fixture pins the sample; one test asserts the default path is the real file.

## Migration Plan

Implement on a git branch named after the change; the README update and the hosted app's redeploy happen when the branch is merged into `main`. Rollback is reverting the merge commit; no stored data is migrated.
