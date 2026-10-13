# route-tariff-calculator Specification

## Purpose

Lets a trader pick a route beginning and ending country on the HU - RS - BG corridor and a booking period, and see the cheapest combination of yearly, quarterly, monthly and daily capacity products for each TSO on the hub-to-hub route, with each point's cost and the route total in EUR/MWh (given an FX rate where the route touches HU).

## Requirements

### Requirement: Route inputs
The Route Tariff Calculator tab SHALL take a route beginning country and a route ending country, each chosen from HU, RS and BG, a booking start date and a booking end date. Both dates are inclusive and are calendar dates only, with no times and no time zones. The tab SHALL NOT have a TSO dropdown or entry and exit point dropdowns.

#### Scenario: Inputs offered
- **WHEN** the tab is opened
- **THEN** it shows a "Route beginning" dropdown and a "Route ending" dropdown, each offering HU, RS and BG, a start date and an end date, and no TSO, entry or exit dropdown

### Requirement: Route price
For every TSO on the route and every product, the TSO's price SHALL be the sum of that product's prices at the TSO's points on the route, each priced part by part where the product's period crosses a tariff change (see tariff-loading "Price-cell meaning"). A TSO's price SHALL be in that TSO's currency per 1 unit of its capacity unit for the whole product period (FGSZ HUF per kWh/h, Gastrans EUR per kWh/h, Bulgartransgaz EUR per kWh/d). Prices of different TSOs SHALL NOT be added together before they are converted to EUR/MWh.

#### Scenario: Summing entry and exit
- **WHEN** the route is BG to HU, and for December 2026 the Gastrans monthly price is 1.36 EUR per kWh/h at the entry Kireevo/Zaychar (BG>RS) and 2.34 at the exit Kiskundorozsma 2 (RS>HU)
- **THEN** the Gastrans monthly price for December 2026 is 3.70 EUR per kWh/h

#### Scenario: A TSO with one point
- **WHEN** the route is BG to HU
- **THEN** the Bulgartransgaz price is the price of the exit Kireevo/Zaychar (BG>RS) alone, in EUR per kWh/d, and the FGSZ price is the price of the entry Kiskundorozsma 2 (RS>HU) alone, in HUF per kWh/h

### Requirement: Optimization
The system SHALL, for each TSO on the route separately, find the cheapest way to cover every day of the booking period from calendar-aligned yearly (gas year), quarterly, monthly and daily products, using that TSO's prices and one shared product choice for all of that TSO's points on the route. Different TSOs MAY choose different products for the same days. A yearly, monthly or quarterly product MAY cover days outside the booking period (over-booking) when that is cheaper than covering only the requested days. The system SHALL optimise each TSO in its own currency and unit and SHALL never depend on the FX rate. The rules for each TSO are:
1. Every calendar month the period touches is priced at the lower of its monthly price and the sum of the daily prices of the requested days in that month.
2. Every calendar quarter (Oct-Dec, Jan-Mar, Apr-Jun, Jul-Sep) the period touches is priced at the lower of its quarterly price and the sum of the prices its touched months have under rule 1.
3. Every gas year (1 October - 30 September) the period touches is priced at the lower of its yearly price and the sum of the prices its touched quarters have under rule 2.
4. Monthly, quarterly and yearly products are always whole calendar months, quarters and gas years; there are no rolling windows.
5. When two choices cost the same, the coarser product is chosen (gas year over quarters, quarter over months, month over days).
Each product is priced part by part where its period crosses a tariff change (see tariff-loading "Price-cell meaning"), the same way as on the Capacity Fee Calculator. A yearly, monthly or quarterly product that has no applicable tariff row on some day of its period lying before the booking period is not an option; the other products are used instead, without a message.

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

#### Scenario: Yearly product across a 1 January tariff change
- **WHEN** a TSO's rows change on 2027-01-01, its `Year` cell is 3.97 before and 4.10 from that date, and the period is gas year 2026/27
- **THEN** the yearly product is compared with the other products at 3.97 x 92/365 + 4.10 x 273/365, not at 3.97

#### Scenario: FX rate does not change the choice
- **WHEN** the same route and period are calculated with the FX rate 380 and with 420
- **THEN** every TSO chooses the same products both times

### Requirement: Results panel
For a valid request the tab SHALL show:
1. One table of every network point on the route in route order, with the TSO, the cleaned name with flow, the EIC, the direction, the capacity type (Firm or Interruptible), the products the point books (see Product labels) and the point's EUR/MWh (see Cost per MWh).
2. A note when any product of any TSO covers days outside the booking period, saying which TSO over-books how many days and why.
3. A route total in EUR/MWh with the cheapest combination and, where there is one, the comparison with the next shorter products and the saving (see Next shorter product comparison).
4. A collapsible "Details" section, closed by default, with one row per point and booked product giving the product's dates (for a yearly, monthly or quarterly product, its whole gas year, calendar month or quarter, even when part of it lies outside the booking period), the product type (yearly, quarterly, monthly or daily), the tariff used: the `Valid from` of every row that point's product was priced from, each marked as open-ended when its `Valid to` is blank, and, as the last column, the tariff: the point's price cell for that product exactly as in the tariff file, in the point's own currency and unit (e.g. "0.1211087 EUR per kWh/d"), one value per row when the product's period crosses a tariff change; for daily products the price of one day, followed by "per day" (several values when the rows change within the days).
The tab SHALL NOT show separate product tables per TSO, a summary per TSO, or any figure in a TSO's own currency and unit. When any point on the route uses Interruptible capacity, the tab SHALL say that Interruptible capacity can be interrupted by the TSO. Alternatives that the optimizer rejected SHALL NOT be shown.

#### Scenario: Point list for BG to HU
- **WHEN** the route is BG to HU
- **THEN** the point table lists, in this order, Bulgartransgaz exit Kireevo/Zaychar (BG>RS), Gastrans entry Kireevo/Zaychar (BG>RS), Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU), all Firm

#### Scenario: Interruptible points flagged
- **WHEN** the route is HU to BG
- **THEN** the FGSZ exit Kiskundorozsma 2 (HU>RS), the Gastrans entry Kiskundorozsma 2 (HU>RS) and the Gastrans exit Kireevo/Zaychar (RS>BG) are listed as Interruptible, the Bulgartransgaz entry Kireevo/Zaychar (RS>BG) as Firm, and a note says Interruptible capacity can be interrupted

#### Scenario: One table on the real tariffs
- **WHEN** the real tariffs are loaded, the route is BG to HU, the period is 2026-10-01 to 2027-03-31 and the FX rate is 400
- **THEN** the point table has the columns #, TSO, Point, EIC, Direction, Capacity type, Products and EUR/MWh; every point's products read "Q4 2026, Q1 2027"; the EUR/MWh cells read 1.4431, 0.8494, 0.9684 and 0.4348; and no per-TSO product table or summary per TSO is shown

#### Scenario: Table content
- **WHEN** a valid route and period produce a result with an FX rate where one is needed
- **THEN** every point row shows its products and its EUR/MWh, points of the same TSO show the same products, and the EUR/MWh cells add up to the route's cheapest combination

#### Scenario: Saving against all-daily
- **WHEN** a valid route and period produce a result
- **THEN** the tab shows no all-daily figure and no saving against all-daily products; the saving it shows is the one against the next shorter products

#### Scenario: Over-booking note
- **WHEN** the period is 2026-10-02 to 2026-12-30 and every TSO books the whole of Q4
- **THEN** every point's products read "Q4 2026 (+2 days)", and a note says each TSO over-books 2 days outside the booking period because that is cheaper

#### Scenario: Details section
- **WHEN** a valid route and period produce a result
- **THEN** a "Details" section, closed until opened, lists for every point each booked product with its dates, product type, tariff used and tariff

#### Scenario: Exact tariff in its own unit
- **WHEN** the real tariffs are loaded, the route is BG to HU, the period is 2026-10-01 to 2027-03-31, and Bulgartransgaz books Q4 2026 at the exit Kireevo/Zaychar (BG>RS)
- **THEN** that Details row's tariff reads "0.1211087 EUR per kWh/d", and the Gastrans entry Kireevo/Zaychar (BG>RS) row for Q4 2026 reads "1.88 EUR per kWh/h"

#### Scenario: Product priced from two rows
- **WHEN** a point's booked gas year is priced from the row valid from 2026-01-01 to 2026-12-31 and the row valid from 2027-01-01
- **THEN** its Details row's tariff used names both rows and its tariff gives both `Year` cells, in that order

### Requirement: Cost per MWh
Each point's cost SHALL be the sum, over the products its TSO books, of that point's own price for the product (priced part by part where the product's period crosses a tariff change; for daily days, the sum of the point's daily prices), so that a TSO's cost is the sum of its points' costs. A point's per-MWh figure SHALL be its cost divided by the energy one unit of its capacity carries on the requested days, times 1000, which assumes the booked capacity is used fully: for a point priced per kWh/h, cost / (24 x requested days) x 1000; for a point priced per kWh/d, cost / requested days x 1000. The figure is in the point's currency; an FGSZ point's HUF/MWh is converted to EUR/MWh by dividing by the FX rate, and the EUR points' figures are already EUR/MWh. The route's EUR/MWh SHALL be the sum of its points' EUR/MWh figures, which equals the sum of its TSOs' figures. Over-booked days outside the period add to the cost but not to the energy.

#### Scenario: Forty-two day period
- **WHEN** the period is 42 days and an FGSZ point's cost is 2145.47 HUF per kWh/h
- **THEN** its HUF/MWh figure is 2145.47 / (24 x 42) x 1000 = 2128.44246, which the FX rate turns into its EUR/MWh

#### Scenario: Bulgartransgaz per kWh/d
- **WHEN** the period is a 365-day gas year and a Bulgartransgaz point's cost is 0.981251 EUR per kWh/d
- **THEN** its EUR/MWh figure is 0.981251 / 365 x 1000 = 2.68836 (shown as 2.6884), with no division by 24

#### Scenario: Two points of one TSO
- **WHEN** the real tariffs are loaded, the route is BG to HU, the period is 2026-10-01 to 2027-03-31 (182 days) and Gastrans books Q4 2026 and Q1 2027, priced 1.88 and 1.83 EUR per kWh/h at the entry Kireevo/Zaychar (BG>RS) and 2.14 and 2.09 at the exit Kiskundorozsma 2 (RS>HU)
- **THEN** the entry's EUR/MWh is 3.71 / (24 x 182) x 1000 = 0.8494, the exit's is 4.23 / (24 x 182) x 1000 = 0.9684, and together they are Gastrans' 1.8178

#### Scenario: Route total
- **WHEN** on a BG to HU route the Bulgartransgaz point is 2.0000 EUR/MWh, the two Gastrans points 1.0000 and 2.0000 EUR/MWh and the FGSZ point 2000 HUF/MWh with the FX rate 400
- **THEN** the route total is 2.0000 + 1.0000 + 2.0000 + 5.0000 = 10.0000 EUR/MWh

#### Scenario: Over-booked days are not counted
- **WHEN** the period is 2026-10-02 to 2026-12-30 (90 days) and a point priced per kWh/h books the whole of Q4 (92 days)
- **THEN** its per-MWh figure divides by 24 x 90, not 24 x 92

### Requirement: FX rate box
The tab SHALL show an input box for the day's HUF-per-EUR rate only when the route touches HU (begins or ends in HU). It SHALL start blank and be required for the EUR figures that depend on FGSZ: with no rate, the EUR/MWh of every Gastrans and Bulgartransgaz point is shown, the FGSZ point's EUR/MWh cell is left empty, and the route total is not shown, with a prompt to enter the rate. With a valid positive rate, the FGSZ point's EUR/MWh SHALL equal its HUF/MWh divided by the rate, and the rate used SHALL be shown ("at 1 EUR = X HUF"). A zero, negative or non-numeric rate SHALL show a message and no FGSZ or route EUR figure. A route that does not touch HU SHALL show all figures, including the route total, without a rate.

#### Scenario: Route without HU
- **WHEN** the route is BG to RS
- **THEN** there is no FX box and every point's EUR/MWh and the route total are shown

#### Scenario: No rate entered
- **WHEN** the route is BG to HU and the FX box is blank
- **THEN** the Bulgartransgaz and Gastrans points show their EUR/MWh, the FGSZ point's EUR/MWh cell is empty, and the route total is not shown, with a prompt to enter the rate

#### Scenario: Rate entered
- **WHEN** the rate 400 is entered and the FGSZ point's HUF/MWh is exactly 2128.4
- **THEN** its EUR/MWh is 5.3210 (2128.4 / 400) and "at 1 EUR = 400 HUF" is shown

#### Scenario: Invalid rate
- **WHEN** the rate is 0 or "abc"
- **THEN** a message says the rate must be a positive number and no FGSZ or route EUR figure is shown

### Requirement: Display precision
The tab SHALL show every price and cost figure (EUR/MWh, HUF/MWh, HUF per kWh/h, EUR per kWh/h and EUR per kWh/d) with 4 decimals, except the tariffs in the "Details" section, which SHALL be shown exactly as in the tariff file, without rounding or trailing zeros. Rounding is for display only and SHALL NOT influence which products the optimizer chooses or the route total.

#### Scenario: Four decimals
- **WHEN** EUR/MWh is 5.32100000
- **THEN** it is displayed as 5.3210

#### Scenario: Exact tariff
- **WHEN** a tariff cell is 375.627714 HUF per kWh/h
- **THEN** the Details section shows it as 375.627714, not 375.6277

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

### Requirement: Product labels
A point's Products cell SHALL name the products it books, in date order, separated by ", ": a yearly product as "GY 2026/27" (the gas year 1 October 2026 - 30 September 2027); a quarterly product as "Q4 2026"; a monthly product as "Dec 2026", and a run of two or more consecutive monthly products as "Nov 2026 - Feb 2027 (monthly)"; daily days in one calendar month as "daily 01-15 Jan 2027", or "daily 05 Jan 2027" for a single day. A product that covers days outside the booking period SHALL be followed by "(+N days)" ("(+1 day)" for one); for a run of monthly products the days outside of all its months are added up and shown as "(monthly, +N days)". Points of the same TSO SHALL show the same products.

#### Scenario: Two quarters
- **WHEN** a point books Q4 2026 and Q1 2027 for 2026-10-01 to 2027-03-31
- **THEN** its products read "Q4 2026, Q1 2027"

#### Scenario: Gas year
- **WHEN** a point books the yearly product for 2026-10-01 to 2027-09-30
- **THEN** its products read "GY 2026/27"

#### Scenario: Monthly run with over-booking
- **WHEN** the period is 2026-11-10 to 2027-02-20 and a point books November 2026 to February 2027 as monthly products
- **THEN** its products read "Nov 2026 - Feb 2027 (monthly, +17 days)"

#### Scenario: Month and days
- **WHEN** the period is 2026-12-05 to 2027-01-15 and a point books December 2026 as a monthly product and 1 to 15 January 2027 as daily products
- **THEN** its products read "Dec 2026 (+4 days), daily 01-15 Jan 2027"

### Requirement: Next shorter product comparison
For each TSO whose cheapest plan uses a product longer than daily, the system SHALL find its comparison plan: the cheapest cover of the same period by the same optimisation rules, using only the product types shorter than the longest type in its cheapest plan (longest yearly: quarterly, monthly and daily; longest quarterly: monthly and daily; longest monthly: daily only). A TSO whose cheapest plan is daily only has no comparison plan and counts with its cheapest cost. The comparison's EUR/MWh SHALL be computed like the cheapest figure (requested days only), the route's comparison SHALL be the sum over its TSOs, and the saving SHALL be the route's comparison minus its cheapest combination, never negative. The route total SHALL show "Cheapest combination", then the comparison line and "Saving". The comparison line SHALL read "Without yearly products", "Without quarterly products" or "Without monthly products" when every TSO with a comparison plan has the same longest type, and otherwise "Next shorter products" with a note naming each TSO's comparison. When no TSO has a comparison plan, the route total SHALL show only the cheapest combination.

#### Scenario: Quarters on the real tariffs
- **WHEN** the real tariffs are loaded, the route is BG to HU, the period is 2026-10-01 to 2027-03-31, the FX rate is 400 and every TSO books Q4 2026 and Q1 2027
- **THEN** the route total shows Cheapest combination 3.6957, Without quarterly products 3.9913 and Saving 0.2956 EUR/MWh

#### Scenario: Different longest products
- **WHEN** FGSZ's cheapest plan is the yearly product and Bulgartransgaz's and Gastrans' are quarterly products
- **THEN** FGSZ is compared without yearly products and the other two without quarterly products, the line reads "Next shorter products", and a note says "FGSZ without yearly; Bulgartransgaz, Gastrans without quarterly"

#### Scenario: Monthly compared with daily
- **WHEN** every TSO's longest product is monthly
- **THEN** each TSO's comparison plan uses daily products only and the line reads "Without monthly products"

#### Scenario: Daily only
- **WHEN** every TSO's cheapest plan uses only daily products
- **THEN** the route total shows only the cheapest combination, with no comparison and no saving line
