## 1. Project setup

- [x] 1.1 Create the package layout (`core/`, `app.py`, `tests/`, `data/sample/`, `data/private/`) and verify the expected files and folders exist
- [x] 1.2 Add dependencies (Streamlit, pandas, openpyxl, pytest) in a requirements file and verify a clean install and `pytest` collect with no errors
- [x] 1.3 Add `.gitignore` rules (`data/private/`, `*.xlsx`, `!data/sample/*.xlsx`) and verify with `git check-ignore -v` that a file in `data/private/` is ignored and one in `data/sample/` is not
- [x] 1.4 Move the synthetic sample to `data/sample/` and verify `git status` shows it as the only tracked xlsx

## 2. Calendar and money helpers

- [x] 2.1 Implement gas-year, calendar-quarter and calendar-month helpers (including leap-year February and the Oct-Dec / Jan-Mar / Apr-Jun / Jul-Sep quarters) and verify unit tests for 2028 February and a period crossing 1 October pass
- [x] 2.2 Implement exact-decimal money helpers with the largest-remainder split and verify a test that months always sum to the whole-HUF total (including the 1,565,115 HUF example splitting into 527,376 / 510,363 / 527,376)

## 3. Tariff loading (spec: tariff-loading)

- [x] 3.1 Implement reading the sheet and validating required columns, and verify a file missing `Q1_Jan` returns a message naming that column and not an exception
- [x] 3.2 Implement in-scope row validation (blank or non-numeric dates and prices excluded and reported by row) and verify a test with a blank `D_Dec` cell
- [x] 3.3 Implement the FGSZ / Firm / Entry-or-Exit filter and the reshape to a normalized table with the `M_Maj`-style month mapping, and verify Interruptible and `WD_*` data never appear
- [x] 3.4 Implement the by-date row lookup (containment, open-ended blank `Valid to`, multi-gas-year rows, no-tariff result) and verify the four scenarios in the spec
- [x] 3.5 Implement the source report (`Valid from`, open-ended flag) and verify the text "from 2026-10-01 (open-ended)"
- [x] 3.6 Implement the configured path and optional uploader override with cached parsing, and verify the default loads the sample and a different path loads that file

## 4. Network points (spec: fgsz-network-points)

- [x] 4.1 Implement the explicit 12-row point table (cleaned name, EIC, direction) and verify a test that it has 7 entries and 5 exits and no excluded points
- [x] 4.2 Implement label building (tab 1 "name (EIC)", tab 2 with direction) and verify 12 distinct tab 2 labels
- [x] 4.3 Implement matching of tariff rows to points by EIC and direction and verify the Balassagyarmat and Kiskundorozsma look-alike scenarios
- [x] 4.4 Verify against the sample that each of the 12 points has at least one Firm row valid on 2026-10-01

## 5. Route optimizer (spec: route-tariff-calculator)

- [x] 5.1 Implement route pricing (entry price plus exit price for the same product and period) and verify the 400 + 300 = 700 scenario
- [x] 5.2 Implement the month pass (full month = min(monthly, sum of days); partial = daily) and verify partial-edge and full-month scenarios with hand-built prices
- [x] 5.3 Implement the quarter pass with tie handling and verify both the quarter-cheaper and quarter-dearer scenarios flip when prices are swapped
- [x] 5.4 Verify the gas-year-boundary scenario (2026-09-20 to 2026-10-10 splits into two daily segments with different rows)
- [x] 5.5 Implement route validity errors (end before start, invalid date, same EIC, no tariff) and verify each returns a message and no exception
- [x] 5.6 Implement the all-daily baseline, saving and totals (HUF per kWh/h, HUF/MWh, EUR/MWh with a positive rate only) and verify the 42-day 2128.4425 HUF/MWh example and that HUF/MWh of exactly 2128.4 gives 5.3210 EUR/MWh at rate 400

## 6. Capacity fee calculator (spec: capacity-fee-calculator)

- [x] 6.1 Implement period resolution for gas year, quarter, month and day and verify "2026 Q4" gives 2026-10-01 to 2026-12-31
- [x] 6.2 Implement price-cell selection and the kWh/d to kWh/h conversion with exact decimals and verify the Kiskundorozsma 2 (RS>HU) 2026 Q4 example gives 1,565,115 HUF
- [x] 6.3 Implement the monthly breakdown for gas year (12), quarter (3), month (1) and day (1) and verify every case sums exactly to the total
- [x] 6.4 Implement capacity validation and the no-tariff message and verify 0 and "abc" and a pre-data gas year return messages

## 7. Streamlit app

- [x] 7.1 Build the two-tab shell with the TSO dropdown (FGSZ only) and verify by running the app that both tabs render with the file loaded
- [x] 7.2 Build tab 1 (entry, exit, dates, FX box that starts blank) and verify by running the app that HUF figures show without a rate and EUR/MWh appears with one, in 4 decimals
- [x] 7.3 Build the tab 1 results table with the "Tariff used" column, the all-daily baseline and the saving, and verify against the tab 1 demo run
- [x] 7.4 Build tab 2 (point with direction in the label, instrument and period pickers, capacity) with the results and invoice table, and verify against the tab 2 demo run
- [x] 7.5 Build the file uploader and the validation message display, and verify uploading a file without `Q1_Jan` shows a plain-language message

## 8. Demo and acceptance

- [x] 8.1 Rewrite the README demo as two FGSZ-only runs (tab 1: Mosonmagyaróvár AT>HU to Kiskundorozsma HU>RS, 2026-10-01 to 2027-03-31; tab 2: Kiskundorozsma 2 RS>HU, 2026 Q4, 50,000 kWh/d) and verify both run in the app
- [x] 8.2 Add acceptance tests for the monthly breakdown sum, an impossible route giving a message, the gas-year split, open-ended rows, and quarter versus three months, and verify all pass in one `pytest` run
- [x] 8.3 Run the app once against a local copy of the real export outside git and verify it loads or reports problems in plain language; verify `git status` shows no private file
