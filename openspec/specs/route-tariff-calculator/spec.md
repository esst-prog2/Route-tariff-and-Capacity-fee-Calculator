# route-tariff-calculator Specification

## Purpose

Lets a trader pick an FGSZ entry point, an FGSZ exit point and a booking period, and see the cheapest combination of quarterly, monthly and daily capacity products for that route, with the cost expressed per kWh/h, per MWh and (given an FX rate) in EUR/MWh.

## Requirements

### Requirement: Route inputs
The Route Tariff Calculator tab SHALL take a TSO, one entry point, one exit point, a booking start date and a booking end date. Both dates are inclusive and are calendar dates only, with no times and no time zones. A route is one entry point plus one exit point of the same TSO.

#### Scenario: Inputs offered
- **WHEN** the tab is opened
- **THEN** it shows a TSO dropdown, an entry dropdown with 7 points, an exit dropdown with 5 points, a start date and an end date

### Requirement: Route validity
The system SHALL reject a request with a clear message, without failing, when: the end date is before the start date; a date is blank or invalid; the entry and exit have the same EIC (the same physical point); or no tariff row applies to the entry or to the exit on some date of the period.

#### Scenario: End before start
- **WHEN** the end date is before the start date
- **THEN** the tab shows a message that the period is invalid and shows no result

#### Scenario: Same physical point
- **WHEN** the entry is Csanádpalota (RO>HU) and the exit is Csanádpalota (HU>RO)
- **THEN** the tab shows a message that the route is not possible

#### Scenario: No tariff for the dates
- **WHEN** the period starts before the earliest tariff row of the entry point
- **THEN** the tab shows a message that no tariff exists for those dates, naming the point

### Requirement: Route price
For any product and period, the route price SHALL be the entry price plus the exit price for that same product, each taken from the tariff row valid on the period's first day. All prices are HUF per 1 kWh/h for the whole product period.

#### Scenario: Summing entry and exit
- **WHEN** the entry monthly price for December is 400 and the exit monthly price for December is 300
- **THEN** the route monthly price for December is 700

### Requirement: Optimization
The system SHALL find the cheapest way to cover every day of the booking period from calendar-aligned yearly (gas year), quarterly, monthly and daily products, using route prices and one shared product choice for entry and exit. A yearly, monthly or quarterly product MAY cover days outside the booking period (over-booking) when that is cheaper than covering only the requested days. The system SHALL work in HUF and never depend on the FX rate. The rules are:
1. Every calendar month the period touches is priced at the lower of its monthly route price and the sum of the daily route prices of the requested days in that month.
2. Every calendar quarter (Oct-Dec, Jan-Mar, Apr-Jun, Jul-Sep) the period touches is priced at the lower of its quarterly route price and the sum of the prices its touched months have under rule 1.
3. Every gas year (1 October - 30 September) the period touches is priced at the lower of its yearly route price and the sum of the prices its touched quarters have under rule 2.
4. Monthly, quarterly and yearly products are always whole calendar months, quarters and gas years; there are no rolling windows.
5. When two choices cost the same, the coarser product is chosen (gas year over quarters, quarter over months, month over days).
Each product is priced from the tariff row valid on its first day. A yearly, monthly or quarterly product whose first day lies before the booking period and has no applicable tariff row is not an option; the other products are used instead, without a message.

#### Scenario: Partial edge months are daily
- **WHEN** the period is 2026-12-05 to 2027-01-15 and, in each of the two months, the daily route prices of the requested days add up to less than the monthly route price
- **THEN** every day is priced with daily prices

#### Scenario: Partial month over-booked
- **WHEN** the period is 2026-11-02 to 2026-11-28 and the November monthly route price is lower than the sum of the daily route prices of those 27 days
- **THEN** the whole of November is booked as one monthly product and 3 days are shown as outside the period

#### Scenario: Full month inside the period
- **WHEN** the period is 2026-11-15 to 2027-01-15, the December monthly route price is lower than the sum of its 31 daily route prices, and the partial months' daily prices are lower than their monthly prices
- **THEN** December is booked as a monthly product and the two partial months as daily

#### Scenario: Quarter cheaper than three months
- **WHEN** the period is 2026-10-01 to 2026-12-31 and the Q4 route price is lower than the sum of the three monthly prices
- **THEN** the result uses the quarterly product

#### Scenario: Quarter dearer than three months
- **WHEN** the period is 2026-10-01 to 2026-12-31 and the Q4 route price is higher than the sum of the three monthly prices
- **THEN** the result uses three monthly products

#### Scenario: Partial quarter over-booked
- **WHEN** the period is 2026-10-02 to 2026-12-30 and the Q4 route price is lower than the cheapest cover of those 90 days by months and days
- **THEN** the whole of Q4 is booked as one quarterly product and 2 days are shown as outside the period

#### Scenario: Over-booking product without a tariff
- **WHEN** the tariff rows start on 2026-10-15 and the period is 2026-10-15 to 2026-11-30
- **THEN** neither the October monthly product nor the Q4 quarterly product is used, 15 to 31 October are priced daily, and no message is shown

#### Scenario: Gas-year boundary
- **WHEN** the period is 2026-09-20 to 2026-10-10 and daily products are cheaper than the September and October monthly products and the Q3 and Q4 quarterly products
- **THEN** 20 to 30 September are priced daily from the tariff row valid on those dates, 1 to 10 October are priced daily from the row valid from 2026-10-01, and the two parts appear as separate segments

### Requirement: Results panel
The tab SHALL show a table with one row per chosen segment giving the segment's dates (for a monthly or quarterly product, the product's whole calendar month or quarter, even when part of it lies outside the booking period), the product (quarterly, monthly or daily), the route price in HUF per kWh/h, the number of days the segment covers outside the booking period, and a "Tariff used" column giving the `Valid from` of the entry row and of the exit row (marking a row as open-ended when its `Valid to` is blank). Consecutive daily days in one calendar month form one segment. When any segment covers days outside the booking period, the tab SHALL show a note saying how many days are over-booked and why. Below the table it SHALL show the all-daily baseline for the requested days and the saving against it, and the totals in HUF per kWh/h, HUF/MWh and EUR/MWh. Alternatives that the optimizer rejected SHALL NOT be shown.

#### Scenario: Table content
- **WHEN** a valid route and period produce a result
- **THEN** each segment row shows its dates, product, price, days outside the period and tariff used, and the total equals the sum of the segment prices

#### Scenario: Over-booking note
- **WHEN** the period is 2026-10-02 to 2026-12-30 and the result books the whole of Q4
- **THEN** the segment reads 2026-10-01 to 2026-12-31 with 2 days outside the period, and a note says 2 days outside the booking period are over-booked because that is cheaper

#### Scenario: Saving against all-daily
- **WHEN** the optimized total is lower than the all-daily total
- **THEN** the saving equals the all-daily total minus the optimized total

### Requirement: Cost per MWh
The HUF/MWh figure SHALL be the total route price in HUF per kWh/h divided by (24 x the number of requested days in the booking period) and multiplied by 1000, which assumes the booked capacity is used fully on the requested days. Over-booked days outside the period add to the cost but not to the energy.

#### Scenario: Forty-two day period
- **WHEN** the period is 42 days and the total route price is 2145.47 HUF per kWh/h
- **THEN** the HUF/MWh figure is 2145.47 / (24 x 42) x 1000 = 2128.44246 (shown as 2128.4425)

#### Scenario: Over-booked days are not counted
- **WHEN** the period is 2026-10-02 to 2026-12-30 (90 days) and the result books the whole of Q4 (92 days)
- **THEN** the HUF/MWh figure divides by 24 x 90, not 24 x 92

### Requirement: FX rate box
The tab SHALL have an input box for the day's HUF-per-EUR rate. It SHALL start blank and be required for EUR figures: with no rate, the route cost in HUF is shown and the EUR/MWh figure is not. With a valid positive rate, EUR/MWh SHALL equal HUF/MWh divided by the rate and SHALL be shown together with the rate used ("at 1 EUR = X HUF"). A zero, negative or non-numeric rate SHALL show a message and no EUR figure.

#### Scenario: No rate entered
- **WHEN** a result is shown and the FX box is blank
- **THEN** HUF figures are shown and the EUR/MWh figure is not

#### Scenario: Rate entered
- **WHEN** the rate 400 is entered and HUF/MWh is exactly 2128.4
- **THEN** EUR/MWh is 5.3210 (2128.4 / 400) and "at 1 EUR = 400 HUF" is shown

#### Scenario: Invalid rate
- **WHEN** the rate is 0 or "abc"
- **THEN** a message says the rate must be a positive number and no EUR figure is shown

### Requirement: Display precision
The tab SHALL show EUR/MWh, HUF/MWh and HUF per kWh/h with 4 decimals. Rounding is for display only and SHALL NOT influence which products the optimizer chooses.

#### Scenario: Four decimals
- **WHEN** EUR/MWh is 5.32100000
- **THEN** it is displayed as 5.3210
