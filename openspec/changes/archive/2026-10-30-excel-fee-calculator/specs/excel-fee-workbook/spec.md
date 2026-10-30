## Purpose

Gives colleagues the Capacity Fee Calculator as one Excel workbook that they open from a shared folder, with dropdowns and the same figures as tab 2 of the app, built from the tariff file and checked against the app.

## ADDED Requirements

### Requirement: Workbook file
The workbook SHALL be one plain `.xlsx` file with formulas only and no macros, external links, data connections or add-ins, so that it opens and calculates in Microsoft 365 or Excel 2021 for Windows without any "Enable content" prompt. Its text SHALL be in English. It SHALL work in any Excel language and regional setting (for example Hungarian, with decimal commas), with dates shown as YYYY-MM-DD. It SHALL have one visible sheet, "Calculator", which holds all inputs and results. The data and calculation sheets SHALL be hidden. The Calculator sheet SHALL be protected without a password, so that formulas cannot be overwritten by accident while the input cells stay editable, and anyone who needs to can unprotect it.

#### Scenario: Opening from the server
- **WHEN** a colleague opens the workbook from a company folder in Excel 2021
- **THEN** it opens without a macro or content warning, shows only the Calculator sheet, and the results are calculated

#### Scenario: Formulas are safe from typing over
- **WHEN** the user tries to type into a result cell of the Calculator sheet
- **THEN** Excel refuses because the sheet is protected, while the input cells accept typing

### Requirement: Workbook inputs
The Calculator sheet SHALL take the same inputs as the app's tab 2 (see capacity-fee-calculator "Fee inputs"), each in its own labelled cell:
- a booking type dropdown with Bundled, Single side and LNG entry;
- a TSO dropdown, used only for Single side, which offers every TSO with a single side by its full name;
- a point dropdown whose list follows the booking type (and, for Single side, the TSO). It uses the labels of fgsz-network-points: bundled point labels, single-side labels with " - Interruptible" where it applies, or LNG entry labels;
- a product instrument dropdown with Gas year, Quarter, Month and Day;
- a period dropdown whose list follows the instrument and the point: gas years as "2026/27", quarters as "2026 Q4" and months as "2026-10". It covers the years of capacity-fee-calculator "Product instruments", from the earliest tariff row of the point (for a bundle, the later of its two sides) to two gas years after the date the workbook is opened;
- a day cell that takes a date, used only for the Day instrument;
- a requested capacity cell;
- a capacity unit dropdown with kWh/h and kWh/d.

Inputs that do not apply to the current choice SHALL be greyed out, and a note SHALL say they are not used. A freshly built workbook SHALL open on Bundled, Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ), Quarter, 2026 Q4, an empty capacity and kWh/h.

#### Scenario: Points follow the booking type and TSO
- **WHEN** the booking type is Single side and the TSO is Gastrans
- **THEN** the point dropdown offers the 4 Gastrans points, and with booking type LNG entry it offers the 14 LNG entries and the TSO cell is greyed out

#### Scenario: Period list follows the instrument
- **WHEN** the instrument is changed from Quarter to Gas year
- **THEN** the period dropdown offers gas years such as "2026/27" instead of quarters such as "2026 Q4"

#### Scenario: Default unit
- **WHEN** a freshly built workbook is opened
- **THEN** the capacity unit is kWh/h and the dropdown offers kWh/h and kWh/d

### Requirement: Outdated and invalid inputs
Excel keeps a dropdown's value when the dropdown it depends on changes. So when the point, TSO or period cell holds a value that is not in its current list, the workbook SHALL show no result and SHALL show a message asking to choose that input again from its list (for example "Choose a point from the list."). A blank, zero, negative or non-numeric capacity SHALL show "Capacity must be a positive number." and no result. A missing day for the Day instrument SHALL show "Choose a product period." and no result.

#### Scenario: Point left over from another booking type
- **WHEN** a bundled point is chosen and the booking type is then changed to LNG entry
- **THEN** no result is shown and the sheet asks to choose a point from the list

#### Scenario: Period left over from another instrument
- **WHEN** the period is "2026 Q4" and the instrument is changed to Month
- **THEN** no result is shown and the sheet asks to choose a period from the list

#### Scenario: Invalid capacity
- **WHEN** the capacity is 0 or "abc"
- **THEN** the sheet shows "Capacity must be a positive number." and no result

### Requirement: Same calculation as the app
For every valid input, the workbook SHALL give the same results as the app's tab 2. That means the same rules as capacity-fee-calculator "Fee calculation", "Monthly invoice breakdown", "Currency" and "Bundle EUR total":
- the conversion between kWh/h and kWh/d;
- the price cell matching the instrument;
- each TSO's tariff decimals (Gas Connect Austria: 4, halves up);
- part-by-part pricing over a tariff change;
- equal months for the TSOs and products that invoice so;
- totals rounded to whole HUF or to cents;
- monthly amounts that add up exactly to the total, with leftover units going to the months with the largest fractional parts, earlier months first on a tie;
- the bundle's EUR total from the rounded side totals.

The rule lists (each TSO's currency, unit, tariff decimals and equal-month products) SHALL come from the app's own rule tables when the workbook is built. Each displayed figure (capacity, price values, total, every monthly amount and the EUR total) SHALL equal the app's to the shown unit.

#### Scenario: Demo quarter
- **WHEN** the input is Single side, FGSZ, Kiskundorozsma 2 RS>HU, Quarter 2026 Q4, 50,000 kWh/d, on the tariff data where the Q4 price is 751.255428
- **THEN** the capacity is 2,083.33 kWh/h, the total is 1,565,115 HUF, and the invoice is 521,705, 521,705 and 521,705 HUF

#### Scenario: Bundle with Gas Connect Austria rounding and EUR total
- **WHEN** the input is Bundled, Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ), Quarter 2026 Q4, 50,000 kWh/d, and the HUF per 1 EUR cell holds 395.5
- **THEN** the exit side costs 2,605.83 EUR (868.61 three times), the entry side costs 782,558 HUF (260,853, 260,853, 260,852), the note says Gas Connect Austria bills its tariff rounded to 4 decimals, and the bundle total is 4,584.48 EUR

#### Scenario: Gas year across a tariff change in equal months
- **WHEN** the input is the Gas Connect Austria exit Mosonmagyaróvár (AT>HU), Gas year 2026/27, 50,000 kWh/d
- **THEN** the price shows 3.9700 and 4.1000 with their dates, the total is 8,473.96 EUR, October to December are 689.24 EUR each, January to April 711.81 and May to September 711.80

#### Scenario: Price per kWh/d
- **WHEN** the input is Bulgartransgaz Kireevo/Zaychar (BG>RS), Quarter 2026 Q4, 1,000 kWh/h
- **THEN** the capacity is shown as 24,000 kWh/d and the total is 5,813.21 EUR, invoiced by days

### Requirement: Workbook results
For each side of the booking, under the inputs, the Calculator sheet SHALL show what the app shows:
- a heading with the point and the product period (start to end dates);
- the TSO and the direction;
- the capacity in the side's unit, to 2 decimals;
- the price cell used, with each of its distinct values once, in date order, to 4 decimals, together with the `Valid from` of each row (and "open-ended" when `Valid to` is blank) and the dates each row covers when there are several;
- the note "<TSO> bills its tariff rounded to <n> decimals." where it applies;
- a warning when the capacity is Interruptible;
- the total in the side's currency;
- a monthly invoice table (month as YYYY-MM, days, amount) with a Total line;
- the equal-month caption where it applies (for example "FGSZ invoices each month as 1/3 of the quarter at the tariff valid in it, whatever the month's number of days.").

Amounts SHALL be labelled with their currency. For a bundle, the sheet SHALL show both sides. It SHALL also show one rate cell for each currency other than EUR that a TSO in scope bills in (CZK, HUF, PLN and RON), labelled "<currency> per 1 EUR" and blank in a freshly built workbook. The cells the booking does not need SHALL be greyed out and marked as not used, so that a typed rate stays with its currency when the bundle changes. The sheet SHALL then show either the bundle's EUR total with the rates used, or a message naming the missing or invalid rate(s). A booking with no tariff for the period SHALL show the app's message naming the point (or, for a bundle, the side) and the first day without a tariff, and no amounts.

#### Scenario: Rate missing
- **WHEN** the default bundle is calculated and the HUF per 1 EUR cell is blank
- **THEN** both sides and their invoices are shown, and instead of the EUR total the sheet says "Enter the HUF per EUR rate to see the EUR total."

#### Scenario: Both sides in EUR
- **WHEN** the bundled point is Kulata/Sidirokastron BG>GR (Bulgartransgaz + DESFA)
- **THEN** every rate cell is greyed out as not used and the EUR total is shown straight away

#### Scenario: No tariff for the period
- **WHEN** a gas year is chosen for a point and a side has no tariff row on the first day of the period
- **THEN** the sheet shows that no tariff exists for that side on that day, and shows no amounts

### Requirement: Building and updating the workbook
The workbook SHALL be built by a command in the repository from a tariff file. By default this is the committed real tariff file, and another file can be given. The build SHALL use the app's tariff loading (with its exclusions and warnings) and the app's point catalog, so that the workbook offers exactly the app's points: on the real tariff file, 43 bundled points, 109 single sides and 14 LNG entries. Tariff prices SHALL come only from the tariff file, never from the code. The Calculator sheet SHALL show the name of the tariff file it was built from and the build date. A tariff file that the app rejects SHALL stop the build with the app's message and write no workbook. After a new tariff export, running the command again SHALL give an up-to-date workbook. The workbook built from the real tariff file SHALL be kept in the repository at `excel/capacity_fee_calculator.xlsx`.

#### Scenario: Rebuild after a new export
- **WHEN** the command is run on a new tariff export
- **THEN** the workbook's points, years and prices follow the new file, and the sheet names that file and the build date

#### Scenario: Rejected file
- **WHEN** the command is run on a file missing the `Year` column
- **THEN** it stops with the app's missing-column message and no workbook is written

### Requirement: Checked against the app
The repository SHALL contain a check that opens the built workbook in Excel and enters inputs into the Calculator sheet. For each input, it SHALL compare every displayed figure with the app's calculation for the same input. The inputs SHALL include every scenario figure of this spec and of capacity-fee-calculator. They SHALL also include, for every point, at least one gas year, one quarter, one month and one day, in both capacity units. Where Excel is not installed, the check SHALL be skipped, not failed.

#### Scenario: Every point agrees with the app
- **WHEN** the check runs on a computer with Excel
- **THEN** for every point and instrument it tried, each figure on the Calculator sheet equals the app's figure, and any difference fails the check, naming the input and the figure
