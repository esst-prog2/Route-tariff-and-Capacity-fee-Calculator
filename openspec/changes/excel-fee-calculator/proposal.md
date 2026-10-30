## Why

The Capacity Fee Calculator (tab 2) currently lives only in the Streamlit app, and it needs Python or a link to the running app. Colleagues should be able to price a capacity booking in a single Excel file that they open from the company server folders, with dropdowns instead of typing, and get the same figures as the app.

## What Changes

- New Excel workbook, the **Capacity Fee Workbook**: a plain `.xlsx` file with formulas only (no macros), for Microsoft 365 / Excel 2021, in English. It does everything tab 2 does:
  - booking type (Bundled / Single side / LNG entry), with point dropdowns that depend on it (and a TSO dropdown for Single side);
  - product instrument (gas year, quarter, month, day) and a period dropdown that depends on the instrument, plus a date cell for a day;
  - requested capacity with a unit dropdown (kWh/h by default, or kWh/d);
  - for each side: TSO, direction, capacity in the side's unit, the price cell and its distinct values with their `Valid from` dates, an Interruptible warning, the total in the side's currency and a monthly invoice that adds up exactly;
  - the Gas Connect Austria 4-decimal rounding note and the equal-month caption;
  - for a bundle, rate boxes and the EUR total;
  - the same messages as the app for an invalid capacity, an outdated choice in a dropdown and a missing tariff.
- New Python script `build_workbook.py` (logic in `core/workbook.py`). It builds the workbook from the tariff file using the app's own loader and point catalog. You run it again after each new tariff export. The tariff data, the point lists and the TSO rules (currency, unit, tariff decimals, equal-month products) go into hidden data sheets. The input sheet is the only visible sheet.
- The built workbook is committed at `excel/capacity_fee_calculator.xlsx`, so it can be copied straight to the server.
- New tests:
  - pytest tests check the workbook's structure and data.
  - A check drives real Excel (through PowerShell COM). It recalculates the workbook for the spec's scenario figures and for many point/instrument/period combinations, and compares each result with `core/fee.py`. It is skipped when Excel is not installed.
- README section on building, updating and sharing the workbook.
- The Streamlit app and its specs do not change.

## Capabilities

### New Capabilities
- `excel-fee-workbook`: The Excel version of the Capacity Fee Calculator: what the workbook offers and shows, how it follows the capacity-fee-calculator rules, how it is built from the tariff file and kept up to date, and how its results are checked against the app.

### Modified Capabilities
<!-- None: the app's tab 2 and the tariff loading rules stay as they are; the workbook follows them. -->

## Impact

- **New code:** `core/workbook.py` and `build_workbook.py`. The builder reuses `core.tariffs`, `core.points`, `core.periods`, `core.money` and the rule tables in `core.fee` (`TARIFF_DECIMALS`, `EQUAL_MONTH_INSTRUMENTS`, `CAPACITY_UNITS`).
- **New files:** `excel/capacity_fee_calculator.xlsx` (built), plus new tests under `tests/`.
- **Dependencies:** none new. openpyxl 3.1.5 is already pinned. The Excel check uses Windows PowerShell and an installed Excel, both optional.
- **Upkeep:** a future fee-rule change on tab 2 must also change the workbook (and this spec). The comparison check catches it if the workbook is forgotten.
