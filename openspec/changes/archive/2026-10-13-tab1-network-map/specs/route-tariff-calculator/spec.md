## ADDED Requirements

### Requirement: Route map
The Route Tariff Calculator tab SHALL show a minimal map that draws only the borders of the 15 countries a route can begin or end in (see the network topology in fgsz-network-points), with each country's code written in its middle, and a marker on the border for each of the 22 map points, placed at the point's location. The map SHALL be zoomed to the area of the border points and country labels, not to whole countries, so that the markers stay apart; parts of countries outside that area (such as eastern Ukraine) are cut at the map's edge. Markers of points that lie very close together SHALL be set slightly apart so that each can be clicked. Pointing at a marker SHALL show the point's name and the two countries it connects. Clicking a marker SHALL add that point to the route (see Route validity for points that cannot be added). The markers of the points already on the route SHALL be highlighted and the route drawn in order. Next to the map, a "Next point" dropdown SHALL offer only the map points that border the country the route has reached, and choosing one SHALL add it to the route exactly as a click does. Under the map the route SHALL be shown as text, alternating countries and points ("BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU"), with a "Remove last" button that removes the last point and a "Clear" button that removes every point.

#### Scenario: Map content
- **WHEN** tab 1 is opened on the real tariff file
- **THEN** the map shows the borders and codes of AT, BG, CR, CZ, DE, GR, HU, IT, NL, PL, RO, RS, SI, SK and UA and 22 point markers, and no marker for Stara Zagora, Komotini or Nea Mesimvria

#### Scenario: Two points on one border
- **WHEN** the route has reached BG
- **THEN** both Negru Voda 1/Kardam and Ruse/Giurgiu are separate markers on the BG - RO border and both are offered by the "Next point" dropdown

#### Scenario: Next point follows the route
- **WHEN** the route is BG > Kireevo/Zaychar > RS
- **THEN** the "Next point" dropdown offers Kireevo/Zaychar and Kiskundorozsma 2 only, and choosing Kiskundorozsma 2 makes the route BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU

#### Scenario: Remove last and clear
- **WHEN** the route is BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU and "Remove last" is pressed
- **THEN** the route is BG > Kireevo/Zaychar > RS; pressing "Clear" then leaves only BG and no result is shown

## MODIFIED Requirements

### Requirement: Route inputs
The Route Tariff Calculator tab SHALL take a route beginning country from the 15 countries of the network topology, the route's border points in the order the gas crosses them (chosen on the route map or with the "Next point" dropdown, see Route map), a booking start date and a booking end date. The route ends in the country the last point leads to. Both dates are inclusive and are calendar dates only, with no times and no time zones. The tab SHALL NOT have a route ending dropdown, a TSO dropdown or entry and exit point dropdowns. The tab SHALL open with the route beginning BG and the points Kireevo/Zaychar and Kiskundorozsma 2, which is the route BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU; changing the beginning country SHALL clear the points.

#### Scenario: Inputs offered
- **WHEN** the tab is opened
- **THEN** it shows a "Route beginning" dropdown offering the 15 countries, the route map with the "Next point" dropdown, the route text "BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU", a start date and an end date, and no route ending, TSO, entry or exit dropdown

#### Scenario: Changing the beginning clears the route
- **WHEN** the route is BG > Kireevo/Zaychar > RS and the beginning is changed to HU
- **THEN** the route is HU with no points and no result is shown

### Requirement: Route points
A route SHALL be hub to hub: it starts with the gas in the beginning country's system and ends with it in the system of the country the last point leads to. At each chosen point, crossing from country X into country Y, the route SHALL use the exit with flow X>Y of the TSO that operates the point on X's side and the entry with flow X>Y of the TSO that operates it on Y's side (see the network topology in fgsz-network-points), each Firm, or Interruptible where that side has no Firm row. The points SHALL be listed in the order crossed. A route SHALL NOT include an entry in the beginning country or an exit from the ending country. Where a country has several TSOs, the entry and the exit used in it MAY belong to different TSOs; each TSO is optimised separately as before.

#### Scenario: BG to HU
- **WHEN** the route is BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU
- **THEN** its points are Bulgartransgaz exit Kireevo/Zaychar (BG>RS), Gastrans entry Kireevo/Zaychar (BG>RS), Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU)

#### Scenario: RS to HU
- **WHEN** the route is RS > Kiskundorozsma 2 > HU
- **THEN** its points are Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU)

#### Scenario: HU to BG
- **WHEN** the route is HU > Kiskundorozsma 2 > RS > Kireevo/Zaychar > BG
- **THEN** its points are FGSZ exit Kiskundorozsma 2 (HU>RS), Gastrans entry Kiskundorozsma 2 (HU>RS), Gastrans exit Kireevo/Zaychar (RS>BG) and Bulgartransgaz entry Kireevo/Zaychar (RS>BG)

#### Scenario: RS to BG
- **WHEN** the route is RS > Kireevo/Zaychar > BG
- **THEN** its points are Gastrans exit Kireevo/Zaychar (RS>BG) and Bulgartransgaz entry Kireevo/Zaychar (RS>BG)

#### Scenario: BG to HU through Romania
- **WHEN** the route is BG > Ruse/Giurgiu > RO > Csanádpalota > HU
- **THEN** its points are Bulgartransgaz exit Ruse/Giurgiu (BG>RO), Transgaz entry Ruse/Giurgiu (BG>RO), Transgaz exit Csanádpalota (RO>HU) and FGSZ entry Csanádpalota (RO>HU)

#### Scenario: Two TSOs in one country
- **WHEN** the route is HU > Mosonmagyaróvár > AT > Tarvisio/Arnoldstein > IT
- **THEN** its points are FGSZ exit and Gas Connect Austria entry Mosonmagyaróvár (HU>AT), both Interruptible, then Trans Austria Gasleitung exit and Snam Rete Gas entry Tarvisio/Arnoldstein (AT>IT), and Gas Connect Austria and Trans Austria Gasleitung are optimised as two TSOs

### Requirement: FX rate box
The tab SHALL show one rate box for each currency other than EUR among the TSOs on the route, labelled as that currency per 1 EUR (for example "HUF per 1 EUR"); a route whose TSOs are all in EUR SHALL show no rate box. The boxes SHALL start blank. A point's EUR/MWh SHALL be shown once its currency is EUR or its currency's box holds a positive number, and is its per-MWh figure in its own currency divided by that rate; until then its EUR/MWh cell is left empty. The route total (and the comparison and saving) SHALL be shown only when every box holds a positive number, together with the rates used ("at 1 EUR = X HUF"); otherwise a prompt names the rates still needed. A zero, negative or non-numeric rate SHALL show a message, and the points in that currency and the route total SHALL show no EUR figure. The rates SHALL NOT influence which products are chosen.

#### Scenario: Route without HU
- **WHEN** the route is BG > Kireevo/Zaychar > RS
- **THEN** there is no rate box and every point's EUR/MWh and the route total are shown

#### Scenario: No rate entered
- **WHEN** the route is BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU and the HUF box is blank
- **THEN** the Bulgartransgaz and Gastrans points show their EUR/MWh, the FGSZ point's EUR/MWh cell is empty, and the route total is not shown, with a prompt to enter the HUF per EUR rate

#### Scenario: Rate entered
- **WHEN** the rate 400 is entered in the HUF box and the FGSZ point's HUF/MWh is exactly 2128.4
- **THEN** its EUR/MWh is 5.3210 (2128.4 / 400) and "at 1 EUR = 400 HUF" is shown

#### Scenario: Invalid rate
- **WHEN** the HUF rate is 0 or "abc"
- **THEN** a message says the rate must be a positive number and no FGSZ or route EUR figure is shown

#### Scenario: Several currencies
- **WHEN** the route is BG > Ruse/Giurgiu > RO > Csanádpalota > HU
- **THEN** the tab shows a "RON per 1 EUR" box and a "HUF per 1 EUR" box; with only the RON rate typed, the Bulgartransgaz and Transgaz points show their EUR/MWh, the FGSZ cell is empty and the prompt asks for the HUF per EUR rate

#### Scenario: All-EUR route
- **WHEN** the route is AT > Tarvisio/Arnoldstein > IT
- **THEN** there is no rate box and the route total is shown

### Requirement: Cost per MWh
Each point's cost SHALL be the sum, over the products its TSO books, of that point's own price for the product (priced part by part where the product's period crosses a tariff change; for daily days, the sum of the point's daily prices), so that a TSO's cost is the sum of its points' costs. A point's per-MWh figure SHALL be its cost divided by the energy one unit of its capacity carries on the requested days, times 1000, which assumes the booked capacity is used fully: for a point priced per kWh/h, cost / (24 x requested days) x 1000; for a point priced per kWh/d, cost / requested days x 1000. The figure is in the point's currency; a point in HUF, RON, CZK or PLN is converted to EUR/MWh by dividing by its currency's rate (see FX rate box), and the EUR points' figures are already EUR/MWh. The route's EUR/MWh SHALL be the sum of its points' EUR/MWh figures, which equals the sum of its TSOs' figures. Over-booked days outside the period add to the cost but not to the energy.

#### Scenario: Forty-two day period
- **WHEN** the period is 42 days and an FGSZ point's cost is 2145.47 HUF per kWh/h
- **THEN** its HUF/MWh figure is 2145.47 / (24 x 42) x 1000 = 2128.44246, which the HUF rate turns into its EUR/MWh

#### Scenario: Bulgartransgaz per kWh/d
- **WHEN** the period is a 365-day gas year and a Bulgartransgaz point's cost is 0.981251 EUR per kWh/d
- **THEN** its EUR/MWh figure is 0.981251 / 365 x 1000 = 2.68836 (shown as 2.6884), with no division by 24

#### Scenario: Two points of one TSO
- **WHEN** the real tariffs are loaded, the route is BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU, the period is 2026-10-01 to 2027-03-31 (182 days) and Gastrans books Q4 2026 and Q1 2027, priced 1.88 and 1.83 EUR per kWh/h at the entry Kireevo/Zaychar (BG>RS) and 2.14 and 2.09 at the exit Kiskundorozsma 2 (RS>HU)
- **THEN** the entry's EUR/MWh is 3.71 / (24 x 182) x 1000 = 0.8494, the exit's is 4.23 / (24 x 182) x 1000 = 0.9684, and together they are Gastrans' 1.8178

#### Scenario: Route total
- **WHEN** on the route BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU the Bulgartransgaz point is 2.0000 EUR/MWh, the two Gastrans points 1.0000 and 2.0000 EUR/MWh and the FGSZ point 2000 HUF/MWh with the HUF rate 400
- **THEN** the route total is 2.0000 + 1.0000 + 2.0000 + 5.0000 = 10.0000 EUR/MWh

#### Scenario: Over-booked days are not counted
- **WHEN** the period is 2026-10-02 to 2026-12-30 (90 days) and a point priced per kWh/h books the whole of Q4 (92 days)
- **THEN** its per-MWh figure divides by 24 x 90, not 24 x 92

#### Scenario: A point in RON
- **WHEN** a Transgaz point's figure is 40 RON/MWh and the RON rate is 5
- **THEN** its EUR/MWh is 8.0000

### Requirement: Route validity
The system SHALL reject an impossible selection with a clear message, without failing. A clicked or chosen point that does not border the country the route has reached SHALL NOT be added, and the message SHALL name the point, the countries it connects and the country reached ("Not possible: Vyrava (PL - SK) does not border BG."). A point that would take the route into a country already on the route, the beginning country included, SHALL NOT be added either, with a message naming that country. A route with no point yet SHALL show a prompt to choose the first border point and no result. The system SHALL also reject, with a message and no result: an end date before the start date; a blank or invalid date; or a period on some requested day of which no tariff row applies to one of the route's points.

#### Scenario: Same country
- **WHEN** the route is HU > Balassagyarmat > SK > Baumgarten > AT and Mosonmagyaróvár is clicked
- **THEN** the point is not added, because it would take the route back into HU, and a message says the route is not possible because it would enter HU a second time

#### Scenario: Point not on the current country
- **WHEN** the route beginning is BG with no points and Vyrava is clicked
- **THEN** the point is not added and the message reads "Not possible: Vyrava (PL - SK) does not border BG."

#### Scenario: No point yet
- **WHEN** the route beginning is HU and no point is chosen
- **THEN** the tab asks for the first border point and shows no result

#### Scenario: End before start
- **WHEN** the end date is before the start date
- **THEN** the tab shows a message that the period is invalid and shows no result

#### Scenario: No tariff for the dates
- **WHEN** the route is BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU and the period starts on 2025-12-01, before the first Bulgartransgaz EUR row (2026-01-01)
- **THEN** the tab shows a message that no tariff exists for those dates, naming the TSO and the point

## RENAMED Requirements

- FROM: `### Requirement: Corridor route validity`
- TO: `### Requirement: Route validity`
