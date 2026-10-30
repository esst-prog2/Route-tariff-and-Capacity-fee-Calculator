## 1. Baseline

- [x] 1.1 Confirm the branch is `excel-fee-calculator` and that `python -m pytest -q` passes before any change (372 tests)
- [x] 1.2 Spike: write a throwaway openpyxl workbook with a dropdown whose list is `=OFFSET(...)` over a block chosen by another cell, one `SUMPRODUCT` and one `_xlfn.TEXTJOIN`, open it in Excel through PowerShell COM, and verify that the dropdown list and the values are right. This confirms Decisions 1 and 8 before the real build. Record the result in the planning log, and keep nothing in the repo

## 2. Builder: data sheets

- [x] 2.1 Create `core/workbook.py` with `build_workbook(table, catalog, source_name, today)`, writing the hidden `Rules` sheet from `points`, `money.CURRENCY_DECIMALS`, `fee.TARIFF_DECIMALS` and `fee.EQUAL_MONTH_INSTRUMENTS`. Verify with `tests/test_workbook.py`: one row per TSO in scope, Gas Connect Austria with 4 tariff decimals, Gastrans equal months for quarters only
- [x] 2.2 Write the hidden `Points` and `Tariffs` sheets: one stretch per line from `product_parts` over each point's whole range, contiguous per point, with `Valid from`, the open-ended flag and the 29 raw price cells, and each point's first line and count. Verify with tests on the real file: 123 catalog points, stretch counts and dates for Mosonmagyaróvár AT>HU (Gas Connect Austria exit), price cells equal to the tariff file's cells, and a stop with a clear message if a point needs more stretch slots than the layout allows
- [x] 2.3 Write the hidden `Lists` sheet (booking types, instruments, units, TSOs by full name, bundle labels, LNG labels, singles grouped per TSO, block start/length table) using the `fgsz-network-points` labels. Verify with tests: 43 bundles, 14 LNG entries, 109 singles, 4 Gastrans singles, the Interruptible suffix on Kiskundorozsma 2 HU>RS

## 3. Builder: calculation sheet

- [x] 3.1 Write the `Calc` inputs part: resolving the booking type, TSO and point to side ids; the stale-input checks; the period label list (about 60 cells, from the point's earliest gas year to two gas years after `TODAY()`); and the period's first and last day from the label or the day cell. Verify with structure tests and, in the Excel check (6.2), with the "Points follow the booking type and TSO", "Period list follows the instrument" and "Outdated and invalid inputs" scenarios
- [x] 3.2 Write each side block's pricing: the price column, 12 month slots, overlap with the stretch slots, tariff decimals from `Rules`, the month prices, the equal-month or day-weighted product price, the capacity in the side unit and the rounded total with 9-decimal pre-rounding. Verify in the Excel check with the Demo quarter, Bulgartransgaz kWh/d, kWh/h-typed and Gas Connect Austria 0.3415 rounding scenarios
- [x] 3.3 Write the invoice split (floor, leftover, rank by fraction and then month) and the up-to-8 distinct price slots with their dates. Verify in the Excel check with "Sum equals total", "Leftover units go to the first months", "Gastrans quarter in thirds, gas year by days", "Months follow the tariff valid in them" and "Repeated tariff shown once" (8.7600 / 9.6360)
- [x] 3.4 Write the no-tariff check (covered days, first uncovered day, message naming the point or bundle side), and the bundle rate check and EUR total from the rounded side totals. Verify in the Excel check with "One side of a bundle has no tariff", "Rate missing", "Two rates needed" (RON and HUF), "Both sides in EUR" and the 4,584.48 EUR total at 395.5

## 4. Builder: Calculator sheet

- [x] 4.1 Lay out the Calculator sheet:
  - title and the "Built from <file> on <date>" line;
  - input cells with data validation lists (`OFFSET` for point and period, a date for day), a yellow fill, unlocked, and grey conditional formatting for unused inputs;
  - the defaults (Bundled, Mosonmagyaróvár AT>HU, Quarter, 2026 Q4, empty capacity, kWh/h);
  - the message line.

  Verify with structure tests on the validations, defaults and defined names
- [x] 4.2 Lay out the two side result blocks (heading with dates, TSO, direction, capacity, price table, rounding note, Interruptible warning, total, invoice table with Total, equal-month caption) and the rate cells and EUR total. Use number formats instead of `TEXT()`, give every input and result its defined name, and blank whatever does not apply. Verify with structure tests that every named cell exists and no formula uses `TEXT(`
- [x] 4.3 Hide the data sheets, protect the Calculator sheet without a password (input cells unlocked) and set the print area. Verify with a structure test that only Calculator is visible and protected, and that the workbook has no macros, external links or connections

## 5. Command line

- [x] 5.1 Add `build_workbook.py` (`[tariff file] [-o path]`, default `data/real/tariffs_real.xlsx` → `excel/capacity_fee_calculator.xlsx`), printing the load warnings and stopping with the app's message (and no file written) on a rejected file. Verify with tests on the sample file, and on a file without the `Year` column

## 6. Excel check against the app

- [x] 6.1 Add `tests/excel_check.ps1`: it opens a copy of the workbook in invisible Excel, takes a JSON list of cases (named input → value), sets them, recalculates, reads the named results back as JSON, and always closes Excel. Verify by running it by hand on the default inputs
- [x] 6.2 Add `tests/test_workbook_excel.py` (marker `excel`, skipped without Excel). It covers every scenario figure of the `excel-fee-workbook` and `capacity-fee-calculator` specs, plus, for each of the 166 choices (43 bundles, 109 single sides, 14 LNG entries), one gas year, quarter, month and day in both units. It compares each displayed figure with `core.fee` for the same input, and reports any difference by input and figure. Verify that `python -m pytest -m excel` passes with Excel installed and skips cleanly without it
- [x] 6.3 Fix any differences the check finds (in `core/workbook.py`, never by changing the expected figures), until the full check passes on the real tariff file

## 7. Delivery

- [x] 7.1 Build `excel/capacity_fee_calculator.xlsx` from the real tariff file, open it in Excel by hand and click through Bundled, Single side and LNG entry for each instrument. Verify that there is no warning on opening, and that the default bundle with 50,000 kWh/d and 395.5 HUF per EUR shows 2,605.83 EUR, 782,558 HUF and 4,584.48 EUR
- [x] 7.2 Add a README section on what the workbook is, how to build it (`python build_workbook.py`), running the Excel check, rebuilding after a new tariff export, copying it to the server (read-only suggested), and that a tab 2 rule change must also change the workbook. Verify the commands in it run as written
- [x] 7.3 Run the full suite (`python -m pytest -q`, and `-m excel`) and verify that everything passes. Log the decisions taken during implementation in `PLANNING_LOG.md`, and commit on `excel-fee-calculator` (not `main`)
