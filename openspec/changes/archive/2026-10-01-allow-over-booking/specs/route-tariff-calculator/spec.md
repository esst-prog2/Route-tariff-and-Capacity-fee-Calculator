## MODIFIED Requirements

### Requirement: Optimization
The system SHALL find the cheapest way to cover every day of the booking period from calendar-aligned quarterly, monthly and daily products, using route prices and one shared product choice for entry and exit. A monthly or quarterly product MAY cover days outside the booking period (over-booking) when that is cheaper than covering only the requested days. The system SHALL work in HUF and never depend on the FX rate. The rules are:
1. Every calendar month the period touches is priced at the lower of its monthly route price and the sum of the daily route prices of the requested days in that month.
2. Every calendar quarter (Oct-Dec, Jan-Mar, Apr-Jun, Jul-Sep) the period touches is priced at the lower of its quarterly route price and the sum of the prices its touched months have under rule 1.
3. Monthly and quarterly products are always whole calendar months and quarters; there are no rolling windows and no yearly products.
4. When two choices cost the same, the coarser product is chosen (quarter over months, month over days).
Each product is priced from the tariff row valid on its first day. A monthly or quarterly product whose first day lies before the booking period and has no applicable tariff row is not an option; the other products are used instead, without a message.

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
