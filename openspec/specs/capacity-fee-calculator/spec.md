# capacity-fee-calculator Specification

## Purpose

Lets a trader price a specific capacity booking for one product instrument at a bundled border point, a single side or an LNG entry, and see each side's total cost and monthly invoice breakdown in its own currency, with an optional EUR total for a bundle, without any optimization.

## Requirements

### Requirement: Fee inputs
The Capacity Fee Calculator tab SHALL first ask for the booking type: Bundled, Single side or LNG entry. For Bundled it SHALL take one bundled point; for Single side a TSO and one single side of that TSO; for LNG entry one LNG entry (labels as in fgsz-network-points). It SHALL then take a product instrument, a period appropriate to that instrument, and a requested capacity with its unit, chosen from a dropdown next to the capacity box: kWh/h (the default) or kWh/d, where 1 kWh/h is 24 kWh/d. The capacity SHALL be a positive number; a blank, zero, negative or non-numeric capacity SHALL show a message and no result.

#### Scenario: Invalid capacity
- **WHEN** the capacity is 0 or "abc"
- **THEN** the tab shows a message that capacity must be a positive number and shows no result

#### Scenario: Capacity unit choice
- **WHEN** the tab opens
- **THEN** the capacity unit dropdown offers kWh/h and kWh/d, with kWh/h selected

#### Scenario: Points follow the TSO
- **WHEN** the booking type is Single side and the TSO is changed from FGSZ to Gastrans
- **THEN** the point dropdown offers the 4 Gastrans points

#### Scenario: Booking type changes the selection
- **WHEN** the booking type is changed from Single side to LNG entry
- **THEN** the TSO dropdown disappears and one dropdown of the 14 LNG entries is shown

### Requirement: Product instruments
The tab SHALL offer four product instruments: gas year (1 October to 30 September), quarter, month and day. Within-day products SHALL NOT be offered. The period picker SHALL depend on the instrument: gas year is a dropdown such as "2025/26"; quarter is a year dropdown plus Q1 to Q4 shown as "2026 Q4"; month is a month picker; day is a date picker. The year lists SHALL run from the gas year of the earliest tariff row of the point (for a bundled point, the later of its two sides' earliest rows) to two gas years after today's date. A selection with no applicable tariff row (for a bundled point, on either side) SHALL give a message that no tariff exists for it, naming the side that has none.

#### Scenario: Quarter selection
- **WHEN** the user selects the quarter instrument, year 2026 and Q4
- **THEN** the period is 2026-10-01 to 2026-12-31

#### Scenario: Selection before the tariff data
- **WHEN** the user selects a gas year that starts before the earliest tariff row of the point
- **THEN** the tab shows a message that no tariff exists and shows no cost

#### Scenario: One side of a bundle has no tariff
- **WHEN** a bundled point is chosen for a period on whose first day only the exit side has a tariff row
- **THEN** the tab shows a message that no tariff exists for the entry side and shows no cost for either side

### Requirement: Fee calculation
For each side of the booking (one for a single side or LNG entry, two for a bundled point), the system SHALL convert the requested capacity to that side's capacity unit: a capacity typed in the side's own unit is used unchanged, a capacity typed in kWh/d at a point priced per kWh/h is divided by 24, and a capacity typed in kWh/h at a point priced per kWh/d is multiplied by 24. It SHALL compute that side's total cost as that capacity times the side's product price for the price cell that matches the instrument, where for Gas Connect Austria each price cell (EUR per kWh/h) is first rounded to 4 decimals, halves up, as Gas Connect Austria bills it (`Year` for a gas year, `Q4_Oct`/`Q1_Jan`/`Q2_Apr`/`Q3_Jul` for a quarter, the matching `M_*` for a month, the matching `D_*` for a day), where a product whose period crosses a tariff change is priced part by part (see tariff-loading "Price-cell meaning"), except that for FGSZ, Eustream, Gas Connect Austria and NET4GAS a gas year or quarter, and for Gastrans a quarter, is priced as the average of its months' prices (each month the price cell of the row valid in it), so each month counts 1/12 or 1/3 whatever its number of days. Amounts SHALL be computed with exact decimals, not binary floating point. For each side the result SHALL show the TSO, the direction, the capacity in the side's unit, the price cell used with each distinct value it has in the tariff rows the product is priced from, once each in date order (one value when the period has one row, or when the rows share the value), the `Valid from` of each of those rows (open-ended when `Valid to` is blank) with the dates each one covers when there are several, the capacity type when it is Interruptible, and the total in the side's currency, rounded to whole forints for HUF and to cents (two decimals) for EUR, RON, CZK and PLN.

#### Scenario: Demo quarter
- **WHEN** the point is FGSZ Kiskundorozsma 2 (RS>HU), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 751.255428
- **THEN** the capacity is 2083.33 kWh/h and the total is 1,565,115 HUF (2083.333... x 751.255428 = 1,565,115.48, shown in whole forints)

#### Scenario: Gastrans quarter
- **WHEN** the point is Gastrans Kiskundorozsma 2 (RS>HU), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 6.42 EUR per kWh/h
- **THEN** the capacity is 2083.33 kWh/h and the total is 13,375.00 EUR

#### Scenario: Bulgartransgaz quarter without the division by 24
- **WHEN** the point is Bulgartransgaz Kireevo/Zaychar (BG>RS), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 0.242217 EUR per kWh/d
- **THEN** the capacity is shown as 50,000 kWh/d and the total is 12,110.85 EUR (50,000 x 0.242217)

#### Scenario: Capacity typed in kWh/h
- **WHEN** the point is FGSZ Kiskundorozsma 2 (RS>HU), the instrument is 2026 Q4, the capacity is 2,000 kWh/h and the applicable Q4 price is 751.255428
- **THEN** the capacity is 2000.00 kWh/h and the total is 1,502,511 HUF (2000 x 751.255428 = 1,502,510.856)

#### Scenario: Capacity typed in kWh/h at a kWh/d point
- **WHEN** the point is Bulgartransgaz Kireevo/Zaychar (BG>RS), the instrument is 2026 Q4, the capacity is 1,000 kWh/h and the applicable Q4 price is 0.242217 EUR per kWh/d
- **THEN** the capacity is shown as 24,000 kWh/d and the total is 5,813.21 EUR (24,000 x 0.242217 = 5,813.208)

#### Scenario: Bundled quarter, two currencies
- **WHEN** the bundled point is Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ), the instrument is 2026 Q4, the capacity is 50,000 kWh/d, the Gas Connect Austria exit's Q4 price is 1.25082191 EUR per kWh/h in the file and the FGSZ entry's Q4 price is 375.627714 HUF per kWh/h
- **THEN** both sides show 2083.33 kWh/h, the exit side costs 2,605.83 EUR (2083.333... x 1.2508, the price rounded to 4 decimals) and the entry side costs 782,558 HUF

#### Scenario: Gas Connect Austria tariff rounded to 4 decimals
- **WHEN** the point is a Gas Connect Austria point, the capacity is 500,000 kWh/h and the applicable price cell is 0.34148 EUR per kWh/h
- **THEN** the price is 0.3415 and the total is 170,750.00 EUR (500,000 x 0.3415, not 500,000 x 0.34148 = 170,740.00), with a note that Gas Connect Austria bills its tariff rounded to 4 decimals

#### Scenario: Gas year across a calendar-year tariff change
- **WHEN** the point is the Gas Connect Austria exit Mosonmagyaróvár (AT>HU), the instrument is gas year 2026/27, the capacity is 50,000 kWh/d, and the `Year` cell is 3.97 EUR per kWh/h in the row valid from 2026-01-01 to 2026-12-31 and 4.10 in the row valid from 2027-01-01
- **THEN** the price shows both values, 3.97 for 2026-10-01 to 2026-12-31 and 4.10 for 2027-01-01 to 2027-09-30, and the total is 2083.333... x (3 x 3.97 + 9 x 4.10) / 12 = 2083.333... x 4.0675 = 8,473.96 EUR (not 2083.333... x 3.97 = 8,270.83 EUR, and not the day-weighted 8,473.40 EUR)

#### Scenario: Repeated tariff shown once
- **WHEN** the point is the Eustream exit Balassagyarmat (SK>HU) and the instrument is gas year 2025/26, priced from three rows whose `Year` cells are 8.76, 8.76 and 9.636 EUR per kWh/h
- **THEN** the price shows "8.7600 / 9.6360", each value once

### Requirement: Monthly invoice breakdown
For each side of the booking, the system SHALL split that side's total across the calendar months the period spans, in proportion to each month's exact cost: the month's days in the period priced with the tariff of the row valid in that month (see tariff-loading "Price-cell meaning"), which for a period with one tariff row is proportional to the month's number of days, in that side's currency. For FGSZ, Eustream, Gas Connect Austria and NET4GAS a gas year or quarter, and for Gastrans a quarter, SHALL instead be split in proportion to each month's tariff alone, so that with one tariff row each month is exactly 1/12 of a gas year or 1/3 of a quarter whatever its number of days, and the tab SHALL say so under the invoice. The total SHALL first be rounded to the currency's smallest shown unit (whole HUF, or cents for EUR, RON, CZK and PLN); each month's share SHALL be rounded down to that unit, and any remaining units SHALL be given one each to the months with the largest fractional parts, so that the displayed monthly amounts always add up exactly to the displayed total. A gas year gives 12 monthly amounts, a quarter 3, a month 1 and a day 1. A bundled booking SHALL show two breakdowns, one per TSO.

#### Scenario: Sum equals total
- **WHEN** an FGSZ quarterly total of 1,565,115 HUF is split over October, November and December
- **THEN** the monthly amounts are 521,705, 521,705 and 521,705 HUF (1/3 each) and add up to exactly 1,565,115

#### Scenario: Leftover units go to the first months
- **WHEN** a Gas Connect Austria quarterly total of 100.00 EUR is split in thirds
- **THEN** the monthly amounts are 33.34, 33.33 and 33.33 EUR

#### Scenario: Gastrans quarter in thirds, gas year by days
- **WHEN** a Gastrans quarter costs 92.00 EUR and a Gastrans gas year 365.00 EUR
- **THEN** the quarter is invoiced 30.67, 30.67 and 30.66 EUR, and the gas year by days (31.00 for October, 30.00 for November, ..., 28.00 for February 2027)

#### Scenario: Sum equals total in EUR cents
- **WHEN** a Bulgartransgaz quarterly total of 12,110.85 EUR is split by days over October (31 days), November (30) and December (31)
- **THEN** the monthly amounts are 4,080.83, 3,949.19 and 4,080.83 EUR and add up to exactly 12,110.85

#### Scenario: Single-month product
- **WHEN** the instrument is a month or a day
- **THEN** the breakdown has one line equal to the total

#### Scenario: Two invoices for a bundle
- **WHEN** the bundled quarter of Mosonmagyaróvár AT>HU costs 2,605.83 EUR on the exit side and 782,558 HUF on the entry side
- **THEN** the Gas Connect Austria breakdown is 868.61, 868.61 and 868.61 EUR and the FGSZ breakdown is 260,853, 260,853 and 260,852 HUF

#### Scenario: Months follow the tariff valid in them
- **WHEN** the gas year 2026/27 at the Gas Connect Austria exit Mosonmagyaróvár (AT>HU) costs 8,473.96 EUR for 50,000 kWh/d as above
- **THEN** October, November and December 2026 are invoiced at 1/12 of the 2026 tariff (689.24 EUR each) and January to September 2027 at 1/12 of the 2027 tariff (711.81 for January to April, 711.80 for May to September), adding up exactly to 8,473.96

### Requirement: Currency
The tab SHALL show each side's amounts in that side's own currency (the TSO's currency in the tariff-loading table). For a single side or an LNG entry it SHALL NOT convert currencies or ask for an FX rate. For a bundled point, see "Bundle EUR total".

#### Scenario: No FX on tab 2
- **WHEN** the booking type is Single side or LNG entry
- **THEN** there is no FX input

#### Scenario: Labels follow the currency
- **WHEN** the point is an FGSZ point
- **THEN** all amounts are labelled HUF, and when the point is a Gastrans or Bulgartransgaz point they are labelled EUR

### Requirement: Bundle EUR total
For a bundled point, the tab SHALL show one rate box for each side currency other than EUR, labelled as that currency per 1 EUR (for example "HUF per 1 EUR"); a bundle whose sides are both in EUR SHALL show no rate box. The rate boxes SHALL start blank. Once every shown box holds a positive number, the tab SHALL show the bundle's EUR total: the sum of each side's displayed (rounded) total converted to EUR (an EUR side unchanged, any other side divided by its rate), rounded to cents, together with the rates used. Until then each side's cost and breakdown SHALL still be shown, and the EUR total SHALL give way to a message naming the missing rate(s); an invalid rate SHALL show a message, not an error.

#### Scenario: EUR total after the rate is typed
- **WHEN** the bundled quarter of Mosonmagyaróvár AT>HU costs 2,605.83 EUR on the exit side and 782,558 HUF on the entry side, and the user types 395.5 in the "HUF per 1 EUR" box
- **THEN** the bundle total is 4,584.48 EUR (2,605.83 + 782,558 / 395.5 = 2,605.83 + 1,978.65487...), shown with "at 1 EUR = 395.5 HUF"

#### Scenario: Rate missing
- **WHEN** the same bundle is shown and the HUF box is blank
- **THEN** both sides' costs and breakdowns are shown, and instead of the EUR total the tab says that the HUF per EUR rate is needed

#### Scenario: Two rates needed
- **WHEN** the bundled point is Csanádpalota RO>HU (Transgaz + FGSZ)
- **THEN** the tab shows a "RON per 1 EUR" box and a "HUF per 1 EUR" box, and the EUR total appears only when both hold positive numbers

#### Scenario: Both sides in EUR
- **WHEN** the bundled point is Kulata/Sidirokastron BG>GR (Bulgartransgaz + DESFA)
- **THEN** no rate box is shown and the EUR total is shown straight away
