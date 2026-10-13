## MODIFIED Requirements

### Requirement: Route inputs
The Route Tariff Calculator tab SHALL take a route beginning country and a route ending country, each chosen from HU, RS and BG, a booking start date and a booking end date. Both dates are inclusive and are calendar dates only, with no times and no time zones. The tab SHALL NOT have a TSO dropdown or entry and exit point dropdowns.

#### Scenario: Inputs offered
- **WHEN** the tab is opened
- **THEN** it shows a "Route beginning" dropdown and a "Route ending" dropdown, each offering HU, RS and BG, a start date and an end date, and no TSO, entry or exit dropdown

### Requirement: Route price
For every TSO on the route and every product, the TSO's price SHALL be the sum of that product's prices at the TSO's points on the route, each taken from the tariff row valid on the product's first day. A TSO's price SHALL be in that TSO's currency per 1 unit of its capacity unit for the whole product period (FGSZ HUF per kWh/h, Gastrans EUR per kWh/h, Bulgartransgaz EUR per kWh/d). Prices of different TSOs SHALL NOT be added together before they are converted to EUR/MWh.

#### Scenario: Summing entry and exit
- **WHEN** the route is BG to HU, and for December 2026 the Gastrans monthly price is 1.36 EUR per kWh/h at the entry Kireevo/Zaychar (BG>RS) and 2.34 at the exit Kiskundorozsma 2 (RS>HU)
- **THEN** the Gastrans monthly price for December 2026 is 3.70 EUR per kWh/h

#### Scenario: A TSO with one point
- **WHEN** the route is BG to HU
- **THEN** the Bulgartransgaz price is the price of the exit Kireevo/Zaychar (BG>RS) alone, in EUR per kWh/d, and the FGSZ price is the price of the entry Kiskundorozsma 2 (RS>HU) alone, in HUF per kWh/h

### Requirement: Optimization
The system SHALL, for each TSO on the route separately, find the cheapest way to cover every day of the booking period from calendar-aligned quarterly, monthly and daily products, using that TSO's prices and one shared product choice for all of that TSO's points on the route. Different TSOs MAY choose different products for the same days. A monthly or quarterly product MAY cover days outside the booking period (over-booking) when that is cheaper than covering only the requested days. The system SHALL optimise each TSO in its own currency and unit and SHALL never depend on the FX rate. The rules for each TSO are:
1. Every calendar month the period touches is priced at the lower of its monthly price and the sum of the daily prices of the requested days in that month.
2. Every calendar quarter (Oct-Dec, Jan-Mar, Apr-Jun, Jul-Sep) the period touches is priced at the lower of its quarterly price and the sum of the prices its touched months have under rule 1.
3. Monthly and quarterly products are always whole calendar months and quarters; there are no rolling windows and no yearly products.
4. When two choices cost the same, the coarser product is chosen (quarter over months, month over days).
Each product is priced from the tariff row valid on its first day. A monthly or quarterly product whose first day lies before the booking period and has no applicable tariff row is not an option; the other products are used instead, without a message.

#### Scenario: Partial edge months are daily
- **WHEN** the period is 2026-12-05 to 2027-01-15 and, for a TSO, in each of the two months the daily prices of the requested days add up to less than the monthly price
- **THEN** every day is priced with daily prices for that TSO

#### Scenario: Partial month over-booked
- **WHEN** the period is 2026-11-02 to 2026-11-28 and, for a TSO, the November monthly price is lower than the sum of the daily prices of those 27 days
- **THEN** that TSO books the whole of November as one monthly product and 3 days are shown as outside the period

#### Scenario: Full month inside the period
- **WHEN** the period is 2026-11-15 to 2027-01-15 and, for a TSO, the December monthly price is lower than the sum of its 31 daily prices, and the partial months' daily prices are lower than their monthly prices
- **THEN** that TSO books December as a monthly product and the two partial months as daily

#### Scenario: Quarter cheaper than three months
- **WHEN** the period is 2026-10-01 to 2026-12-31 and, for a TSO, the Q4 price is lower than the sum of the three monthly prices
- **THEN** that TSO uses the quarterly product

#### Scenario: Quarter dearer than three months
- **WHEN** the period is 2026-10-01 to 2026-12-31 and, for a TSO, the Q4 price is higher than the sum of the three monthly prices
- **THEN** that TSO uses three monthly products

#### Scenario: TSOs choose independently
- **WHEN** the period is 2026-10-01 to 2026-12-31, the Gastrans Q4 price is lower than its three monthly prices and the FGSZ Q4 price is higher than its three monthly prices
- **THEN** Gastrans uses the quarterly product and FGSZ uses three monthly products

#### Scenario: Partial quarter over-booked
- **WHEN** the period is 2026-10-02 to 2026-12-30 and, for a TSO, the Q4 price is lower than the cheapest cover of those 90 days by months and days
- **THEN** that TSO books the whole of Q4 as one quarterly product and 2 days are shown as outside the period

#### Scenario: Over-booking product without a tariff
- **WHEN** a TSO's tariff rows start on 2026-10-15 and the period is 2026-10-15 to 2026-11-30
- **THEN** that TSO uses neither the October monthly product nor the Q4 quarterly product, 15 to 31 October are priced daily, and no message is shown

#### Scenario: Gas-year boundary
- **WHEN** the period is 2026-09-20 to 2026-10-10 and, for a TSO, daily products are cheaper than the September and October monthly products and the Q3 and Q4 quarterly products
- **THEN** 20 to 30 September are priced daily from the tariff row valid on those dates, 1 to 10 October are priced daily from the row valid from 2026-10-01, and the two parts appear as separate segments

#### Scenario: FX rate does not change the choice
- **WHEN** the same route and period are calculated with the FX rate 380 and with 420
- **THEN** every TSO chooses the same products both times

### Requirement: Results panel
For a valid request the tab SHALL show:
1. A table of every network point on the route in route order, with the TSO, the cleaned name with flow, the EIC, the direction and the capacity type (Firm or Interruptible).
2. For each TSO on the route, a table with one row per chosen segment giving the segment's dates (for a monthly or quarterly product, the product's whole calendar month or quarter, even when part of it lies outside the booking period), the product (quarterly, monthly or daily), the TSO's price in its own currency and unit, the number of days the segment covers outside the booking period, and a "Tariff used" column giving the `Valid from` of the row used at each of the TSO's points (marking a row as open-ended when its `Valid to` is blank). Consecutive daily days in one calendar month form one segment.
3. A note when any segment of any TSO covers days outside the booking period, saying which TSO over-books how many days and why.
4. A summary with one row per TSO giving its cheapest cost, its all-daily cost and its saving in its own currency and unit, per MWh in its own currency, and in EUR/MWh; and rows for the route giving the cheapest total, the all-daily total and the saving in EUR/MWh only.
When any point on the route uses Interruptible capacity, the tab SHALL say that Interruptible capacity can be interrupted by the TSO. Alternatives that the optimizer rejected SHALL NOT be shown.

#### Scenario: Point list for BG to HU
- **WHEN** the route is BG to HU
- **THEN** the point table lists, in this order, Bulgartransgaz exit Kireevo/Zaychar (BG>RS), Gastrans entry Kireevo/Zaychar (BG>RS), Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU), all Firm

#### Scenario: Interruptible points flagged
- **WHEN** the route is HU to BG
- **THEN** the FGSZ exit Kiskundorozsma 2 (HU>RS), the Gastrans entry Kiskundorozsma 2 (HU>RS) and the Gastrans exit Kireevo/Zaychar (RS>BG) are listed as Interruptible, the Bulgartransgaz entry Kireevo/Zaychar (RS>BG) as Firm, and a note says Interruptible capacity can be interrupted

#### Scenario: Table content
- **WHEN** a valid route and period produce a result
- **THEN** each TSO's segment rows show their dates, product, price, days outside the period and tariff used, and each TSO's cheapest cost equals the sum of its segment prices

#### Scenario: Over-booking note
- **WHEN** the period is 2026-10-02 to 2026-12-30 and a TSO books the whole of Q4
- **THEN** that TSO's segment reads 2026-10-01 to 2026-12-31 with 2 days outside the period, and a note says that TSO over-books 2 days outside the booking period because that is cheaper

#### Scenario: Saving against all-daily
- **WHEN** the route's cheapest total is lower than its all-daily total
- **THEN** the route saving in EUR/MWh equals the all-daily total minus the cheapest total, and each TSO's saving equals its all-daily cost minus its cheapest cost

### Requirement: Cost per MWh
Each TSO's per-MWh figure SHALL be its cost divided by the energy one unit of its capacity carries on the requested days, times 1000, which assumes the booked capacity is used fully: for a TSO priced per kWh/h, cost / (24 x requested days) x 1000; for a TSO priced per kWh/d, cost / requested days x 1000. The figure is in the TSO's own currency; FGSZ's HUF/MWh is converted to EUR/MWh by dividing by the FX rate, and the EUR TSOs' figures are already EUR/MWh. The route's EUR/MWh SHALL be the sum of its TSOs' EUR/MWh figures, both for the cheapest combination and for the all-daily baseline. Over-booked days outside the period add to the cost but not to the energy.

#### Scenario: Forty-two day period
- **WHEN** the period is 42 days and FGSZ's cheapest cost is 2145.47 HUF per kWh/h
- **THEN** the FGSZ HUF/MWh figure is 2145.47 / (24 x 42) x 1000 = 2128.44246 (shown as 2128.4425)

#### Scenario: Bulgartransgaz per kWh/d
- **WHEN** the period is a 365-day gas year and Bulgartransgaz's cost is 0.981251 EUR per kWh/d
- **THEN** its EUR/MWh figure is 0.981251 / 365 x 1000 = 2.68836 (shown as 2.6884), with no division by 24

#### Scenario: Route total
- **WHEN** on a BG to HU route Bulgartransgaz is 2.0000 EUR/MWh, Gastrans 3.0000 EUR/MWh and FGSZ 2000 HUF/MWh with the FX rate 400
- **THEN** the route total is 2.0000 + 3.0000 + 5.0000 = 10.0000 EUR/MWh

#### Scenario: Over-booked days are not counted
- **WHEN** the period is 2026-10-02 to 2026-12-30 (90 days) and a TSO priced per kWh/h books the whole of Q4 (92 days)
- **THEN** its per-MWh figure divides by 24 x 90, not 24 x 92

### Requirement: FX rate box
The tab SHALL show an input box for the day's HUF-per-EUR rate only when the route touches HU (begins or ends in HU). It SHALL start blank and be required for the EUR figures that depend on FGSZ: with no rate, every TSO's figures in its own currency are shown, and FGSZ's EUR/MWh and the route's EUR/MWh rows are left empty with a prompt to enter the rate. With a valid positive rate, FGSZ's EUR/MWh SHALL equal its HUF/MWh divided by the rate, and the rate used SHALL be shown ("at 1 EUR = X HUF"). A zero, negative or non-numeric rate SHALL show a message and no FGSZ or route EUR figure. A route that does not touch HU SHALL show all figures, including the route's EUR/MWh, without a rate.

#### Scenario: Route without HU
- **WHEN** the route is BG to RS
- **THEN** there is no FX box and the route's EUR/MWh is shown

#### Scenario: No rate entered
- **WHEN** the route is BG to HU and the FX box is blank
- **THEN** Bulgartransgaz's and Gastrans' EUR/MWh and FGSZ's HUF/MWh are shown, and FGSZ's EUR/MWh and the route's EUR/MWh are not, with a prompt to enter the rate

#### Scenario: Rate entered
- **WHEN** the rate 400 is entered and FGSZ's HUF/MWh is exactly 2128.4
- **THEN** FGSZ's EUR/MWh is 5.3210 (2128.4 / 400) and "at 1 EUR = 400 HUF" is shown

#### Scenario: Invalid rate
- **WHEN** the rate is 0 or "abc"
- **THEN** a message says the rate must be a positive number and no FGSZ or route EUR figure is shown

### Requirement: Display precision
The tab SHALL show every price and cost figure (EUR/MWh, HUF/MWh, HUF per kWh/h, EUR per kWh/h and EUR per kWh/d) with 4 decimals. Rounding is for display only and SHALL NOT influence which products the optimizer chooses or the route total.

#### Scenario: Four decimals
- **WHEN** EUR/MWh is 5.32100000
- **THEN** it is displayed as 5.3210

## ADDED Requirements

### Requirement: Corridor route validity
The system SHALL reject a request with a clear message, without failing, when: the route beginning and the route ending are the same country; the end date is before the start date; a date is blank or invalid; or no tariff row applies to one of the route's points on some requested day of the period.

#### Scenario: Same country
- **WHEN** the route beginning is HU and the route ending is HU
- **THEN** the tab shows a message that the route is not possible and shows no result

#### Scenario: End before start
- **WHEN** the end date is before the start date
- **THEN** the tab shows a message that the period is invalid and shows no result

#### Scenario: No tariff for the dates
- **WHEN** the route is BG to HU and the period starts on 2025-12-01, before the first Bulgartransgaz EUR row (2026-01-01)
- **THEN** the tab shows a message that no tariff exists for those dates, naming the TSO and the point

### Requirement: Route points
A route SHALL be hub to hub: it starts with the gas in the beginning country's system and ends with it in the ending country's system, and it SHALL consist of the exit and the matching entry at every border it crosses, in the order crossed (see the corridor topology in fgsz-network-points). It SHALL NOT include an entry in the beginning country or an exit from the ending country.

#### Scenario: BG to HU
- **WHEN** the route is BG to HU
- **THEN** its points are Bulgartransgaz exit Kireevo/Zaychar (BG>RS), Gastrans entry Kireevo/Zaychar (BG>RS), Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU)

#### Scenario: RS to HU
- **WHEN** the route is RS to HU
- **THEN** its points are Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU)

#### Scenario: HU to BG
- **WHEN** the route is HU to BG
- **THEN** its points are FGSZ exit Kiskundorozsma 2 (HU>RS), Gastrans entry Kiskundorozsma 2 (HU>RS), Gastrans exit Kireevo/Zaychar (RS>BG) and Bulgartransgaz entry Kireevo/Zaychar (RS>BG)

#### Scenario: RS to BG
- **WHEN** the route is RS to BG
- **THEN** its points are Gastrans exit Kireevo/Zaychar (RS>BG) and Bulgartransgaz entry Kireevo/Zaychar (RS>BG)

## REMOVED Requirements

### Requirement: Route validity
**Reason**: Its rule that the entry and exit must not be the same physical point belongs to the FGSZ entry-to-exit routes, which are dropped; a corridor route is never built from two sides of one point.
**Migration**: Replaced by "Corridor route validity", which rejects a route whose beginning and ending are the same country and keeps the period and no-tariff checks.
