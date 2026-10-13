## 1. Branch and test baseline

- [x] 1.1 Create the git branch `all-tsos-tab2` from `main` and verify `python -m pytest -q` passes before any change
- [x] 1.2 Add `tests/conftest.py` with a fixture that pins `FGSZ_TARIFF_FILE` to the synthetic sample for the existing app tests, and verify the full suite still passes unchanged

## 2. Tariff loading

- [x] 2.1 Extend the TSO table in `core/tariffs.py` to the 21 TSOs (code, currency, unit, display name) and make the scope filter an allow-list of them; verify with a test that loading the real file uses no row of the 8 excluded operators and reports none of them
- [x] 2.2 Skip Plinacro's HRK rows silently and drop capacity types other than Firm and Interruptible before the Firm-else-Interruptible choice; verify with tests for the "Plinacro HRK rows skipped silently" and "Other capacity types ignored" scenarios
- [x] 2.3 Make `data/real/tariffs_real.xlsx` the default path; verify with an updated default-path test and the "Configured private file" scenario
- [x] 2.4 Add RON, CZK and PLN with 2 decimals to the currency minor units in `core/money.py`; verify with a rounding and formatting test per currency

## 3. Point catalog

- [x] 3.1 Build the single-side and LNG catalog from the loaded rows with the exclusion set, the name/flow cleaning rule and the override table; verify on the real file: 109 single sides, 14 LNG entries, FGSZ 14, Bulgartransgaz 13, Gastrans 4, and a test listing every cleaned name and flow
- [x] 3.2 Keep the cleaned names of the existing 30 points unchanged and keep the tab 1 corridor resolving to the same points; verify the existing `test_points.py` and `test_route.py` tests pass
- [x] 3.3 Build the bundles (same EIC and flow, different TSOs, both Firm) plus the Baumgarten WAG pairs; verify on the real file: 43 bundles, the Mosonmagyaróvár AT>HU sides, no bundle at the four Interruptible crossings, the two Baumgarten bundles and no TAG Baumgarten bundle
- [x] 3.4 Add the bundle and LNG labels and the full TSO names; verify the label scenarios of the `fgsz-network-points` delta spec in tests

## 4. Fee calculation

- [x] 4.1 Add the bundled fee (two sides priced independently, the later earliest row as the year-list start, "no tariff" naming the side); verify the "Bundled quarter, two currencies" and "One side of a bundle has no tariff" scenarios on the real file
- [x] 4.2 Add the bundle EUR total from the rounded side totals and the typed rates (missing or invalid rates listed); verify the "EUR total after the rate is typed" (4,584.53 EUR at 395.5), "Rate missing", "Two rates needed" and "Both sides in EUR" scenarios
- [x] 4.3 Verify the per-side invoice split with the "Two invoices for a bundle" scenario (878.07 / 849.74 / 878.07 EUR and 263,688 / 255,182 / 263,688 HUF)

## 5. Tab 2 UI

- [x] 5.1 Add the booking-type radio (Bundled / Single side / LNG entry) with a separate point widget per type and the TSO dropdown only for single sides; verify with AppTest that switching type shows the right dropdowns
- [x] 5.2 Show a bundle as two side blocks with their own invoice tables, then the rate boxes for non-EUR sides and the EUR total or the missing-rate message; verify with AppTest on the real file for Mosonmagyaróvár AT>HU 2026 Q4, 50,000 kWh/d, with and without a HUF rate
- [x] 5.3 Show the default file name in the sidebar caption; verify the app starts on the real file with no path configured and tab 1 still prices BG -> HU without errors

## 6. Docs and check

- [x] 6.1 Update the README: real tariffs are the default, the 21 TSOs, the tab 2 booking types with a bundled walk-through on the real data; verify every figure quoted matches the app
- [x] 6.2 Run the full test suite and verify it passes
- [x] 6.3 User checks tab 2 by eye on the real file (a bundle with two currencies, a single side, an LNG entry) and confirms the figures

## 7. Prices across tariff changes (added after the user's check)

- [x] 7.1 Add `product_parts` and the part-by-part product price to `core/tariffs.py`; verify the tariff-loading scenarios "Gas year across a 1 January tariff change", "Quarter across a mid-quarter tariff change" and "Product with one row" in tests
- [x] 7.2 Price tab 2 products part by part, with the parts on `FeeResult` and invoice months weighted by their exact cost; verify "Gas year across a calendar-year tariff change" (8,473.40 EUR) and "Months follow the tariff valid in them" on the real file, and that the earlier tab 2 tests still pass
- [x] 7.3 Show every tariff in tab 2's "Price" metric and caption; verify with AppTest on the real file for the Gas Connect Austria exit Mosonmagyaróvár (AT>HU), gas year 2026/27
- [x] 7.4 Price tab 1's yearly, quarterly and monthly products part by part in `TsoOracle`, with tariff used and the Details tariff covering the whole product period; verify "Yearly product across a 1 January tariff change" and "Product priced from two rows" in tests, and that the existing route and acceptance tests pass
- [x] 7.5 Re-check every README figure against the app after the change and update any that moved; run the full suite and verify it passes
- [x] 7.6 User checks the gas year 2026/27 at the Gas Connect Austria exit Mosonmagyaróvár (AT>HU) on tab 2 by eye and confirms the price and invoice
