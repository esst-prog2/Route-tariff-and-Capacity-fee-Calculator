## MODIFIED Requirements

### Requirement: Fee inputs
The Capacity Fee Calculator tab SHALL take a TSO (FGSZ, Gastrans or Bulgartransgaz), one point from the selected TSO's list (labelled with flow, see fgsz-network-points), a product instrument, a period appropriate to that instrument, and a requested capacity in kWh/d. The capacity SHALL be a positive number; a blank, zero, negative or non-numeric capacity SHALL show a message and no result.

#### Scenario: Invalid capacity
- **WHEN** the capacity is 0 or "abc"
- **THEN** the tab shows a message that capacity must be a positive number and shows no result

#### Scenario: Points follow the TSO
- **WHEN** the TSO is changed from FGSZ to Gastrans
- **THEN** the point dropdown offers the 4 Gastrans points

### Requirement: Fee calculation
The system SHALL convert the requested capacity to the point's capacity unit: for a point priced per kWh/h (FGSZ, Gastrans) by dividing kWh/d by 24, and for a point priced per kWh/d (Bulgartransgaz) by using it unchanged. It SHALL compute the total cost as that capacity times the one price cell that matches the instrument (`Year` for a gas year, `Q4_Oct`/`Q1_Jan`/`Q2_Apr`/`Q3_Jul` for a quarter, the matching `M_*` for a month, the matching `D_*` for a day), taken from the row valid on the first day of the period. Amounts SHALL be computed with exact decimals, not binary floating point. The result SHALL show the capacity in the point's unit, the price cell used, the `Valid from` of the source row (open-ended when `Valid to` is blank), the capacity type when it is Interruptible, and the total in the point's currency, rounded to whole forints for HUF and to cents for EUR.

#### Scenario: Demo quarter
- **WHEN** the point is FGSZ Kiskundorozsma 2 (RS>HU), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 751.255428
- **THEN** the capacity is 2083.33 kWh/h and the total is 1,565,115 HUF (2083.333... x 751.255428 = 1,565,115.48, shown in whole forints)

#### Scenario: Gastrans quarter
- **WHEN** the point is Gastrans Kiskundorozsma 2 (RS>HU), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 6.42 EUR per kWh/h
- **THEN** the capacity is 2083.33 kWh/h and the total is 13,375.00 EUR

#### Scenario: Bulgartransgaz quarter without the division by 24
- **WHEN** the point is Bulgartransgaz Kireevo/Zaychar (BG>RS), the instrument is 2026 Q4, the capacity is 50,000 kWh/d and the applicable Q4 price is 0.242217 EUR per kWh/d
- **THEN** the capacity is shown as 50,000 kWh/d and the total is 12,110.85 EUR (50,000 x 0.242217)

### Requirement: Monthly invoice breakdown
The system SHALL split the total across the calendar months the period spans, in proportion to each month's number of days in the period. The total SHALL first be rounded to the currency's smallest shown unit (whole HUF, or EUR cents); each month's share SHALL be rounded down to that unit, and any remaining units SHALL be given one each to the months with the largest fractional parts, so that the displayed monthly amounts always add up exactly to the displayed total. A gas year gives 12 monthly amounts, a quarter 3, a month 1 and a day 1.

#### Scenario: Sum equals total
- **WHEN** a quarterly total of 1,565,115 HUF is split over October (31 days), November (30) and December (31)
- **THEN** the monthly amounts are 527,376, 510,363 and 527,376 HUF and add up to exactly 1,565,115

#### Scenario: Sum equals total in EUR cents
- **WHEN** a quarterly total of 12,110.85 EUR is split over October (31 days), November (30) and December (31)
- **THEN** the monthly amounts are 4,080.83, 3,949.19 and 4,080.83 EUR and add up to exactly 12,110.85

#### Scenario: Single-month product
- **WHEN** the instrument is a month or a day
- **THEN** the breakdown has one line equal to the total

### Requirement: Currency
The tab SHALL show all amounts in the selected point's own currency (HUF for FGSZ, EUR for Gastrans and Bulgartransgaz) and SHALL NOT convert currencies or ask for an FX rate.

#### Scenario: No FX on tab 2
- **WHEN** the tab is shown
- **THEN** there is no FX input

#### Scenario: Labels follow the currency
- **WHEN** the point is an FGSZ point
- **THEN** all amounts are labelled HUF, and when the point is a Gastrans or Bulgartransgaz point they are labelled EUR
