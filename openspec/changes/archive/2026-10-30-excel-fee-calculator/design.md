## Context

Tab 2's rules live in `core/fee.py`:
- `calculate_fee` and `calculate_bundle_fee` price a booking;
- `TARIFF_DECIMALS` lists the TSOs whose tariff is rounded (Gas Connect Austria: 4 decimals);
- `EQUAL_MONTH_INSTRUMENTS` lists the TSOs and products invoiced in equal months;
- `split_by_weights` (in `core/money.py`) splits a total across months, using the largest-remainder method.

The point catalog (`core/points.py` `build_catalog`) and the stretches where each tariff row applies (`TariffTable.product_parts`, where a later row supersedes an earlier one) are worked out in Python from the tariff file. On the real file the tariff rows cover 135 points, of which the catalog offers 123 (109 singles and 14 LNG entries), plus 43 bundles made of those singles; there are 548 tariff rows. A point has at most 6 rows, and there are 5 currencies.

openpyxl (already pinned, 3.1.5) can write formulas, data validation, conditional formatting, defined names and sheet protection. It does **not** write the metadata Excel needs for dynamic-array (spilling) formulas. A `FILTER` or `SEQUENCE` written by openpyxl opens as an implicit-intersection `@FILTER(...)` and gives one value, or `#NAME?`.

Excel and LibreOffice are installed on the development machine. pywin32 is not installed, but Windows PowerShell can drive Excel through COM.

## Goals / Non-Goals

**Goals:**
- Excel does only arithmetic, lookups and rounding. Everything the app already resolves in Python is resolved when the workbook is built and stored as plain data: which points exist, their labels, which tariff row applies on which days, and each TSO's rules.
- Formulas that work in any Excel language and number format.
- One source of truth for the rules: the builder reads `core.fee`'s tables, and the Excel check compares the workbook with `core.fee`.

**Non-Goals:**
- The Route Tariff Calculator (tab 1) in Excel.
- Updating tariffs inside Excel (decided: the workbook is rebuilt by the script).
- Excel for Mac, Excel Online and LibreOffice are not targets. They may work, but are not checked.
- Translating the workbook to Hungarian.

## Decisions

### 1. No spilling formulas. Dependent dropdowns use `OFFSET` over pre-grouped lists
The builder writes each dropdown's possible lists into a hidden `Lists` sheet, grouped so that each list is one contiguous block:
- bundles, LNG entries and TSOs;
- the singles of each TSO, one block per TSO.

A lookup table gives each block's first row and length. The point cell's data validation is `=OFFSET(Lists!$X$1, start-1, 0, count, 1)`, with start and count found by formulas from the booking type and TSO.

The period list is a fixed column of about 60 formula cells in a hidden `Calc` sheet. They build the labels ("2026/27", "2026 Q4", "2026-10") from the instrument, the point's earliest gas year and `TODAY()`, and the dropdown uses `OFFSET` over the cells that hold a label.

*Alternatives considered:*
- `FILTER`/`SEQUENCE` spills: openpyxl cannot write them correctly (see Context).
- `INDIRECT` over named ranges: it breaks on labels with spaces and accents, and is fragile.

As a result, the workbook uses no function newer than Excel 2019 except where a check proves it works. The target stays 365/2021, as decided. Non-spilling newer functions such as `TEXTJOIN` and `XLOOKUP` (written with their `_xlfn.` prefix) are allowed only if the Excel check passes with them.

### 2. The builder resolves tariff rows into non-overlapping stretches
For each point, the builder calls `product_parts` over the point's whole date range, using the app's own code. It then writes a `Tariffs` sheet with one line per stretch: point id, first day, last day (9999-12-31 when open-ended), the row's `Valid from` and open-ended flag, and its 29 raw price cells. A point's stretches are contiguous and in date order, and a `Points` sheet gives each point's first stretch line and stretch count.

With this, Excel only needs date overlap (`MAX(0, MIN(last, to) - MAX(first, from) + 1)`). It does not need the "later row supersedes" rule, and the rule cannot be implemented twice in two different ways. A gap between stretches is a missing tariff.

*Alternative:* write the raw rows and resolve them in Excel formulas. Rejected because it duplicates logic that already has tests.

### 3. Visible rule tables, filled from `core.fee`
A hidden `Rules` sheet has one row per TSO:
- code and full name;
- currency, unit, and the decimals of the currency;
- tariff decimals (blank for none);
- equal-month for gas year (yes/no) and for quarter (yes/no).

The builder fills it from `points`, `money.CURRENCY_DECIMALS`, `fee.TARIFF_DECIMALS` and `fee.EQUAL_MONTH_INSTRUMENTS`. Formulas look the rules up here, so the Gas Connect Austria rounding and the equal-month lists are not typed into formulas, and a rule change in the app reaches the workbook on the next build.

### 4. Fixed-size calculation blocks in `Calc`
`Calc` has two identical side blocks. Side 1 is the single point or the bundle's exit, and side 2 is the bundle's entry (unused otherwise). Each block has:
- **Point lookup:** id, TSO, direction, currency, unit, capacity type and rules.
- **Period:** first and last day, from the period label or the day cell.
- **The price column number:** Year, the start month's quarter column, `M_*` or `D_*`.
- **12 month slots:** for each, first and last day in the period, days, and the month price. The month price is Σ over the point's stretches (up to the builder's max per point, rounded up to 8 slots) of the rounded cell × overlap days ÷ month days. The tariff decimals are applied with `ROUND(cell, n)`, which is halves away from zero, the same as `round_places` for positive prices.
- **Covered days and the first uncovered day:** for the no-tariff message.
- **The product price:** the average of the month prices for equal-month products, or the day-weighted sum otherwise.
- **The capacity in the side unit and the total:** the exact total, then the rounded total.
- **The invoice:** weights, the exact share per month, floor, the leftover count, then a rank of each month by (fraction descending, month ascending) using `COUNTIFS`/`SUMPRODUCT`, and the final amounts.
- **Up to 8 price slots:** the distinct values in date order, with their `Valid from`, open-ended flag and the dates they cover. A slot is kept only when its value differs from every earlier slot overlapping the period, matching `dict.fromkeys(part_prices)`.

The bundle's EUR total and the rate check also sit in `Calc`. The Calculator sheet only shows `Calc` cells, and shows `""` when they do not apply.

### 5. Floating point is guarded by pre-rounding
Excel calculates in binary floating point, but the app uses exact fractions. Before each rounding decision, the value is first rounded to 6 decimals past the unit being decided: the total to `currency decimals + 6`, each month's share of the minor units to 6 decimals before it is floored and ranked, and the EUR total to 8 decimals. A fixed 9 decimals would exceed double precision on large HUF totals. Noise such as 0.4999999999 or ties between thirds (0.3333…3 vs 0.3333…4) is then removed, and the decision matches exact arithmetic for all real tariffs. A capacity typed in kWh/d is divided by 24 only in the final product (capacity × price ÷ 24), never stored rounded.

### 6. No `TEXT()` for numbers or dates
Format codes inside `TEXT()` depend on the Excel language. So numbers and dates are shown in their own cells, with number formats (`#,##0`, `#,##0.00`, `0.0000`, `yyyy-mm-dd`), which Excel stores independently of the language. Messages that contain a date (for example, the no-tariff day) build it from `YEAR`/`MONTH`/`DAY` with zero padding. The price values are written with `FIXED(value, 4, TRUE)`, which has no format code and uses the Excel language's decimal mark. They are joined with `TEXTJOIN`, so the price shows the same "8.7600 / 9.6360" text as the app ("8,7600 / 9,6360" in Hungarian Excel). The "Tariff used" text is the app's own: "from 2026-01-01 (open-ended) for ...".

### 7. Defined names as the interface
Every input and result cell gets a workbook-level defined name, for example `in_booking`, `in_point`, `in_capacity`, `out1_total`, `out1_amounts` and `msg_main`. The calculation names of the two sides are `sa_*` and `sb_*`. Excel refuses to open a file with a name such as `s1_total`, because it starts like the cell address `S1`. The Excel check and the pytest structure tests address cells only by these names, so the layout can change without breaking them.

### 8. Code layout
- `core/workbook.py`: `build_workbook(table, catalog, source_name, today) -> openpyxl.Workbook`. It is pure, takes the build date as a parameter, and is testable without Excel.
- `build_workbook.py` at the repository root: a command line (`python build_workbook.py [tariff file] [-o excel/capacity_fee_calculator.xlsx]`). It loads the file with `tariffs.load_tariffs`, prints the load warnings, stops on errors, and saves the workbook.
- `tests/test_workbook.py`: checks the structure and data with openpyxl. It needs no Excel and runs in the normal suite.
- `tests/excel_check.ps1` and `tests/test_workbook_excel.py`: Python builds the cases and the expected figures from `core.fee`, then runs the PowerShell script. The script opens a copy of the workbook in invisible Excel, fills the named inputs for each case, recalculates, reads the named results and returns JSON. The test is skipped when Excel or PowerShell COM is unavailable. It is marked so that it can be run on its own (`pytest -m excel`).

### 9. Calculator sheet layout
The Calculator sheet is laid out top to bottom:
1. Title.
2. "Built from <file> on <date>".
3. The input block, with input cells in a light yellow fill (unlocked) and inputs that do not apply greyed out by conditional formatting.
4. One message line.
5. The side 1 block, then the side 2 block: heading, facts, price table, notes and invoice table (12 rows plus Total).
6. The rate cells and the EUR total.

Unused rows are blank. Column widths and print area are set so that it prints on one A4 page per side.

## Risks / Trade-offs

- **[Excel keeps stale dropdown values]** → Each dependent input is checked with `COUNTIF` against its current list, and a "Choose … from the list." message blocks the result (spec "Outdated and invalid inputs").
- **[Floating-point rounding differs from exact fractions at a half]** → Pre-rounding to 9 decimals (Decision 5), plus the Excel check over every point, both units and all instruments. A difference fails the check, naming the input.
- **[The workbook drifts from the app after a rule change]** → The rules come from `core.fee` on every build, a new kind of rule needs a formula change, and the Excel check catches figures that differ. The proposal says rule changes must update this spec too.
- **[Excel is needed to run the full check]** → The structure tests run everywhere, and the Excel check runs on the development machine before a built workbook is committed. The README says so.
- **[Hungarian Excel shows decimal commas and translated function names]** → Excel handles this itself for formulas stored in the file. Only `TEXT()` format codes would break, and they are not used (Decision 6).
- **[A user saves a modified copy over the server file]** → The sheet is protected (no password), and the README suggests making the server copy read-only.
- **[More than 8 stretches for one point in a future export]** → The builder computes the maximum and sizes the slots to it (at least 8). If a file needed more than the layout allows, it would stop with a clear message rather than silently drop rows.

## Migration Plan

This adds a new file, and nothing existing changes. To roll it out, build the workbook, run the Excel check, commit it on `excel-fee-calculator`, merge it when you approve, and copy `excel/capacity_fee_calculator.xlsx` to the server folder. To roll back, delete the file from the server. After each new tariff export, rebuild the workbook, run the check, commit and copy it again.

## Open Questions

- Should the server copy be marked read-only, or "Read-only recommended" through the file's save options? Either can be decided at rollout without changing the workbook.
