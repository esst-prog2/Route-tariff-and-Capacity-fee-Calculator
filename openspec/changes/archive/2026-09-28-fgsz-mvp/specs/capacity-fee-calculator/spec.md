## Purpose

Lets a trader price a specific capacity booking at one FGSZ point for one product instrument and see the total cost in HUF and the monthly invoice breakdown, without any optimization.

## ADDED Requirements

### Requirement: Fee inputs
The Capacity Fee Calculator tab SHALL take a TSO, one point from the shared list of 12 (labelled with direction, see fgsz-network-points), a product instrument, a period appropriate to that instrument, and a requested capacity in kWh/d. The capacity SHALL be a positive number; a blank, zero, negative or non-numeric capacity SHALL show a message and no result.

#### Scenario: Invalid capacity
- **WHEN** the capacity is 0 or "abc"
- **THEN** the tab shows a message that capacity must be a positive number and shows no result

### Requirement: Product instruments
The tab SHALL offer four product instruments: gas year (1 October to 30 September), quarter, month and day. Within-day products SHALL NOT be offered. The period picker SHALL depend on the instrument: gas year is a dropdown such as "2025/26"; quarter is a year dropdown plus Q1 to Q4 shown as "2026 Q4"; month is a month picker; day is a date picker. The year lists SHALL run from the gas year of the earliest tariff row of the point to two gas years after today's date. A selection with no applicable tariff row SHALL give a message that no tariff exists for it.

#### Scenario: Quarter selection
- **WHEN** the user selects the quarter instrument, year 2026 and Q4
- **THEN** the period is 2026-10-01 to 2026-12-31

#### Scenario: Selection before the tariff data
- **WHEN** the user selects a gas year that starts before the earliest tariff row of the point
- **THEN** the tab shows a message that no tariff exists and shows no cost

### Requirement: Fee calculation
The system SHALL convert the requested capacity to kWh/h by dividing kWh/d by 24, and SHALL compute the total cost as that capacity times the one price cell that matches the instrument (`Year` for a gas year, `Q4_Oct`/`Q1_Jan`/`Q2_Apr`/`Q3_Jul` for a quarter, the matching `M_*` for a month, the matching `D_*` for a day), taken from the row valid on the first day of the period. Amounts SHALL be computed with exact decimals, not binary floating point. The result SHALL show the capacity in kWh/h, the price cell used, the `Valid from` of the source row (open-ended when `Valid to` is blank), and the total in HUF.

#### Scenario: Demo quarter
- **WHEN** the point is Kiskundorozsma 2 (RS>HU), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 751.255428
- **THEN** the capacity is 2083.33 kWh/h and the total is 1,565,115 HUF (2083.333... x 751.255428 = 1,565,115.48, shown in whole forints)

### Requirement: Monthly invoice breakdown
The system SHALL split the total across the calendar months the period spans, in proportion to each month's number of days in the period. The total SHALL be rounded to whole HUF first; each month's share SHALL be rounded down to whole HUF, and any remaining forints SHALL be given one each to the months with the largest fractional parts, so that the displayed monthly amounts always add up exactly to the displayed total. A gas year gives 12 monthly amounts, a quarter 3, a month 1 and a day 1.

#### Scenario: Sum equals total
- **WHEN** a quarterly total of 1,565,115 HUF is split over October (31 days), November (30) and December (31)
- **THEN** the monthly amounts are 527,376, 510,363 and 527,376 HUF and add up to exactly 1,565,115

#### Scenario: Single-month product
- **WHEN** the instrument is a month or a day
- **THEN** the breakdown has one line equal to the total

### Requirement: Currency
The tab SHALL show all amounts in HUF, the currency of the FGSZ tariff rows, and SHALL NOT convert currencies or ask for an FX rate.

#### Scenario: No FX on tab 2
- **WHEN** the tab is shown
- **THEN** there is no FX input and all amounts are labelled HUF
