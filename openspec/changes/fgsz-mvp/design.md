## Context

See proposal.md for motivation and specs/ for behavior. Facts that shape the approach, taken from the synthetic sample `DM_Tariff_capacity_fee_20260924123613.xlsx` (sheet `Capacity_fee`, 749 rows, 53 columns; 117 FGSZ rows):

- The file is wide: one row per point, direction, capacity type and validity window, with price columns `Year`, `Q4_Oct`..`Q3_Jul`, `M_Oct`..`M_Sep`, `D_Oct`..`D_Sep` and `WD_*` (ignored). Month columns run in gas-year order, and May is `M_Maj`.
- FGSZ rows are all HUF and kWh/h. The user confirmed each price cell is HUF for 1 kWh/h for the whole product period.
- Validity windows are gas-year rows chained without gaps or overlaps, but some span several gas years (for example 2021-10-01 to 2025-09-30) and the newest rows have a blank `Valid to`.
- One EIC covers both directions of a border point, so identity is (EIC, direction). Source names are inconsistent (`n.a`, "MGT", "/Velké Zlievce", mojibake-prone accents).
- The sample is synthetic: prices are scrambled (Interruptible is often dearer than Firm), so no test may rely on real-world price relationships. In the sample the monthly product beats the sum of days in every cell, and quarterly beats its three months in about 65% of cells; the real export may differ.
- The project decided on Python and Streamlit with a UI-independent `core/` package.

## Goals / Non-Goals

**Goals:**
- Keep all business rules in `core/` as pure, unit-testable functions with no Streamlit import.
- Make every rule in the specs reproducible from small hand-built tariff tables in tests.
- Keep the real export out of the repository and out of the code.

**Non-Goals:**
- Supporting other TSOs, currencies or units beyond what the rows carry for FGSZ (a row's currency and unit are checked, not converted).
- Performance work: the FGSZ Firm border data is a few dozen rows.

## Decisions

**Package layout.** `core/tariffs.py` (load, validate, filter, lookup), `core/points.py` (the 12-point table), `core/periods.py` (gas-year, quarter and month helpers; not named `calendar` so it cannot shadow the standard library), `core/optimizer.py`, `core/fee.py`, `core/money.py` (decimal arithmetic and the largest-remainder split), and a thin `app.py` for Streamlit. The UI only calls `core/` and formats results. Alternative considered: logic inside Streamlit callbacks; rejected because it cannot be tested without the UI.

**Normalized tariff table.** Loading reshapes the wide file into a long table keyed by (EIC, direction, valid_from, valid_to) with a product-price mapping, so lookups take a date and a product and never touch column names. Column-name mapping (including `M_Maj`) lives in one place. Alternative: query the wide frame directly; rejected because month and quarter naming would leak into the calculators.

**Point table is data in code.** The 12 points (cleaned label, EIC, direction) are an explicit table in `core/points.py`, not derived by cleaning strings. Cleaning raw names is fragile (names differ per direction and include exceptions), while 12 fixed rows are easy to review. Rows are matched by EIC and direction only.

**Exact money arithmetic.** Use `decimal.Decimal` (or `fractions.Fraction` for the kWh/d / 24 step) so capacity / 24 x price is exact until the final rounding. Floats are rejected because the breakdown-sums-to-total requirement is a hard test.

**Optimizer as a bottom-up pass over months.** For the period, list the calendar months and, for each, decide full or partial. Full months get min(monthly, sum of daily); partial months get daily prices. Then, for every calendar quarter whose three months are all full, compare the quarterly price with the sum of those three month prices and keep the lower. Prices come from the route (entry price + exit price for the same product) so the choice is shared by both points, as decided. Ties prefer the coarser product (quarter over months over days) for a shorter, more readable booking list. Each product uses the row valid on its first day; since rows change on 1 October, which is a month boundary, no month or quarter ever straddles two rows.

**Route tariff and units.** All optimization is in HUF per kWh/h. HUF/MWh = total / (24 x days) x 1000; EUR/MWh = HUF/MWh / FX. FX is a user-typed value, so the optimizer takes no FX input and cannot depend on it.

**Errors as values.** Calculators return a result or a typed error (invalid period, same point, no tariff for a date, invalid capacity), which the UI renders as messages. Nothing in `core/` raises for user input.

**Data loading.** Path from an environment variable or setting, defaulting to `data/sample/`; an optional Streamlit uploader replaces it per session; parsing is cached per file contents. The real export lives in a gitignored `data/private/`; `.gitignore` ignores `*.xlsx` except `data/sample/*.xlsx`.

**Tests.** Unit tests use small hand-built tables and one synthetic sample; no test depends on real prices. Acceptance tests: (1) the monthly breakdown sums exactly to the total; (2) an impossible route gives a message, not an exception; (3) a period crossing 1 October splits at the boundary with old and new rows; (4) open-ended rows apply to later dates; (5) the quarter-versus-three-months choice flips when the prices are swapped.

## Risks / Trade-offs

- [Sample differs from the real export, for example blanks or extra header text] -> The loader validates columns and rows and reports plain-language messages, and it can be exercised against the real file locally without sharing it.
- [Open-ended rows quote prices for dates after the last published tariff] -> Accepted by the user; the "Tariff used" column shows the source row's `Valid from` and open-ended status.
- [A shared product choice can cost more than optimizing each point separately] -> Accepted by the user; the per-point alternative is a possible later change.
- [Optimizer conclusions rest on synthetic prices] -> Rules are generic comparisons and tests inject their own prices; no price relationship is hardcoded.
- [Same source name may carry inconsistent encoding] -> Match on EIC and direction, never on the name text.
