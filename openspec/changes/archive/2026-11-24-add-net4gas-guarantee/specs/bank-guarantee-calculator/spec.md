## MODIFIED Requirements

### Requirement: Booking inputs
The app SHALL have a third tab, "Bank Guarantee Calculator", after the Route Tariff Calculator and the Capacity Fee Calculator. The tab SHALL take:
- a TSO from a dropdown that offers Eustream, Gas Connect Austria, FGSZ and then NET4GAS, starting on Eustream;
- a network point from a dropdown of that TSO's single sides, labelled as on tab 2;
- a product instrument (gas year, quarter, month or day) and its period, with the same pickers, choices and defaults as tab 2;
- a requested capacity with its unit (kWh/h, the default, or kWh/d), as on tab 2;
- for Eustream only, a stage: "Capacity auction" or "Booked capacity" (the default);
- an "Auction surcharge (%)" box, for every TSO and at either stage, that starts blank and carries the note "The auction surcharge (premium) in %, added to the tariff; leave it blank for none." A blank box means 0%; a decimal comma is accepted.

For Eustream at "Booked capacity" the tab SHALL also take the CEGHIX in EUR/MWh, in a box that starts blank and carries the note "Enter the CEGHIX valid on the day before the booking." For Eustream at "Capacity auction" the CEGHIX box SHALL NOT be shown. For Gas Connect Austria, FGSZ and NET4GAS neither the stage nor the CEGHIX box SHALL be shown. FGSZ and NET4GAS SHALL have no VAT input, and NET4GAS no credit limit input. For a NET4GAS exit point the tab SHALL also take, side by side, an "OTE index (EUR/MWh)" box with the note "The OTE index in EUR/MWh that NET4GAS uses for the variable part." and a "CZK per 1 EUR (variable part)" box with the note "The CZK per EUR rate that NET4GAS uses for the variable part.", both starting blank; a decimal comma is accepted as elsewhere ("24,36" is 24.36, but "107,705" is read as 107,705, so three decimals need a point). For a NET4GAS entry point neither box SHALL be shown.

#### Scenario: CEGHIX box only for booked capacity
- **WHEN** the TSO is Eustream and the stage is "Booked capacity"
- **THEN** the tab shows the CEGHIX box with the note "Enter the CEGHIX valid on the day before the booking."
- **WHEN** the stage is switched to "Capacity auction"
- **THEN** the CEGHIX box is not shown

#### Scenario: Surcharge box at both stages
- **WHEN** the tab opens, and again after the stage is switched to "Capacity auction"
- **THEN** the "Auction surcharge (%)" box is shown, blank

#### Scenario: Eustream and GCA are offered
- **WHEN** the user opens the TSO dropdown
- **THEN** the choices are Eustream, Gas Connect Austria, FGSZ and NET4GAS, in that order, and Eustream is chosen

#### Scenario: Only Eustream is offered
- **WHEN** Eustream is the chosen TSO and the user opens the network point dropdown
- **THEN** it lists only Eustream's single sides (for example "Balassagyarmat SK>HU (21Z000000000358C)"), no GCA, FGSZ or NET4GAS point

#### Scenario: GCA inputs
- **WHEN** the user chooses Gas Connect Austria
- **THEN** the network point dropdown lists GCA's single sides as on tab 2 (for example "Mosonmagyaróvár AT>HU (21Z000000000003C)"), the "Auction surcharge (%)" box is shown, and neither the stage nor the CEGHIX box is shown

#### Scenario: FGSZ inputs
- **WHEN** the user chooses FGSZ
- **THEN** the network point dropdown lists FGSZ's 14 single sides as on tab 2 (for example "Csanádpalota HU>RO (21Z000000000236Q)" and "Mosonmagyaróvár AT>HU (21Z000000000003C)"), the "Auction surcharge (%)" box is shown, and no stage, CEGHIX or VAT input is shown

#### Scenario: NET4GAS inputs
- **WHEN** the user chooses NET4GAS
- **THEN** the network point dropdown lists NET4GAS's 6 single sides as on tab 2 (for example "Lanžhot CZ>SK (21Z000000000061Z)"), the "Auction surcharge (%)" box is shown, and no stage, CEGHIX, VAT or credit limit input is shown
- **WHEN** the point is Lanžhot CZ>SK
- **THEN** the blank OTE index and CZK per 1 EUR (variable part) boxes are shown
- **WHEN** the point is Lanžhot SK>CZ
- **THEN** neither box is shown

### Requirement: List of bookings
An "Add to list" button SHALL add the booking to a list shown as a table. Each row SHALL keep the TSO, surcharge and, for Eustream, the stage and CEGHIX, and for a NET4GAS exit point the OTE index and CZK per EUR rate it was added with. A booking SHALL NOT be added, and a message SHALL be shown instead, in these cases:
- the capacity is invalid: tab 2's message "Capacity must be a positive number.";
- the period has no tariff: tab 2's no-tariff message;
- the surcharge is negative or not a number: "The surcharge must be a percentage of 0 or more.";
- for Eustream at "Booked capacity", the CEGHIX is blank, zero, negative or not a number: "CEGHIX must be a positive number.";
- for a NET4GAS exit point, the OTE index is blank, zero, negative or not a number: "The OTE index must be a positive number.";
- for a NET4GAS exit point, the CZK per EUR rate is blank, zero, negative or not a number: "The CZK per EUR rate must be a positive number."

Adding the same booking more than once SHALL be allowed. Rows of different TSOs and currencies SHALL be allowed in the same list. Rows SHALL be selectable and removed with "Remove selected rows". "Clear list" SHALL empty the list. An empty list SHALL show "Add a booking to start the list." The list SHALL last for the browser session.

#### Scenario: Adding and clearing
- **WHEN** the user adds two valid bookings and then presses "Clear list"
- **THEN** the table first shows two rows, and afterwards "Add a booking to start the list."

#### Scenario: Missing CEGHIX
- **WHEN** the TSO is Eustream, the stage is "Booked capacity", the CEGHIX box is blank and the user presses "Add to list"
- **THEN** the tab shows "CEGHIX must be a positive number." and the list is unchanged

#### Scenario: GCA needs no CEGHIX
- **WHEN** the TSO is Gas Connect Austria and the user adds a valid booking
- **THEN** the booking is added without any CEGHIX

#### Scenario: Negative surcharge
- **WHEN** the surcharge box holds "-5" and the user presses "Add to list"
- **THEN** the tab shows "The surcharge must be a percentage of 0 or more." and the list is unchanged

#### Scenario: Removing a row
- **WHEN** the list has three rows and the user selects the second and presses "Remove selected rows"
- **THEN** the list keeps the first and third rows in their order

#### Scenario: Missing OTE index or rate
- **WHEN** the TSO is NET4GAS, the point is Lanžhot CZ>SK, the OTE index box is blank and the user presses "Add to list"
- **THEN** the tab shows "The OTE index must be a positive number." and the list is unchanged
- **WHEN** the OTE index is filled but the CZK per EUR box is blank
- **THEN** the tab shows "The CZK per EUR rate must be a positive number." and the list is unchanged

### Requirement: Table columns and total
Each row SHALL show these columns, in this order:
- TSO;
- Network point, as name and flow, e.g. "Balassagyarmat SK>HU";
- Product: the instrument and period, e.g. "Quarter 2026 Q4", "Gas year 2025/26", "Month 2027-01", "Day 2026-12-05";
- Capacity, as typed with its unit, with thousands separators, e.g. "100,000 kWh/h";
- Stage;
- Surcharge (%), as typed, e.g. "10" or "2.5", or "–" when there is none (blank or 0);
- CEGHIX (EUR/MWh);
- OTE index (EUR/MWh), as typed;
- CZK per EUR, as typed;
- Currency: EUR for Eustream and Gas Connect Austria, HUF for FGSZ, CZK for NET4GAS;
- Capacity fee;
- GfON fee;
- Commodity / volume fee;
- Capacity fee guarantee;
- GfON fee guarantee;
- Commodity / volume fee guarantee;
- VAT;
- Total guarantee.

The Stage, CEGHIX (EUR/MWh), GfON fee and GfON fee guarantee columns SHALL be shown only when the list holds at least one Eustream row; otherwise they SHALL be left out of both the list and the total table, and the other columns keep their order.

Every amount SHALL be in the row's currency with thousands separators: EUR and CZK with two decimals, HUF in whole forints. For an Eustream row, the Commodity / volume fee, Commodity / volume fee guarantee and VAT cells SHALL show "–". For an Eustream "Capacity auction" row, the CEGHIX, GfON fee and GfON fee guarantee cells SHALL also show "–", and the total guarantee SHALL equal the capacity fee guarantee. For a Gas Connect Austria row, the Stage, CEGHIX, GfON fee, GfON fee guarantee and VAT cells SHALL show "–", and the total guarantee SHALL equal the capacity fee guarantee plus the commodity / volume fee guarantee; for a GCA day row the capacity fee guarantee, commodity / volume fee guarantee and total guarantee cells SHALL also show "–". For an FGSZ row, the Stage, CEGHIX, GfON fee and GfON fee guarantee cells SHALL show "–", and the total guarantee SHALL equal the capacity fee guarantee plus the commodity / volume fee guarantee plus the VAT. For a NET4GAS row, the Stage, CEGHIX, GfON fee, GfON fee guarantee, Commodity / volume fee guarantee and VAT cells SHALL show "–", the Commodity / volume fee cell SHALL show the variable part (0.00 at an entry point), and the total guarantee SHALL equal the capacity fee guarantee. For every row other than a NET4GAS exit row, the OTE index and CZK per EUR cells SHALL show "–".

The OTE index (EUR/MWh) and CZK per EUR columns SHALL be shown only when the list holds at least one NET4GAS exit row; otherwise they SHALL be left out of the list, and the other columns keep their order.

A total table under the list SHALL have one row per currency present in the list, EUR first, then HUF, then CZK, labelled "Total" with that currency in its Currency column; each SHALL add up every amount column of the list's rows in that currency, counting "–" as zero.

For each currency other than EUR present in the list (HUF, CZK), the tab SHALL show under the total table a "<currency> per 1 EUR" box ("HUF per 1 EUR", "CZK per 1 EUR") that starts blank. When every such box holds a positive number (a decimal comma is accepted), the total table SHALL end with a row "All in EUR (1 EUR = <rate> <currency> = <rate> <currency>)", naming each rate in the order of the total rows (e.g. "All in EUR (1 EUR = 400 HUF)" or "All in EUR (1 EUR = 400 HUF = 25 CZK)"), with EUR as its currency, in which each amount column is the EUR total plus each other currency's total divided by its rate, rounded to cents once. While any of these boxes is blank the row SHALL NOT be shown; when one holds anything else the tab SHALL show "The <currency> per EUR rate must be a positive number." (e.g. "The HUF per EUR rate must be a positive number.") and SHALL NOT show the row.

When the list holds at least one Gas Connect Austria day row, the tab SHALL show under the table the note "Gas Connect Austria asks no security deposit for day contracts: they are covered by its one-off activation deposit of EUR 100,000, which is not included in the total."

#### Scenario: Total of a mixed list
- **WHEN** the list holds the Balassagyarmat SK>HU rows of the scenarios below: 2026 Q4 booked (total guarantee 280,104.80), January 2027 booked (140,060.40) and 5 December 2026 at auction (7,896.00)
- **THEN** the total row's total guarantee is 428,061.20 EUR

#### Scenario: Total of a list with both TSOs
- **WHEN** the list holds Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, booked, CEGHIX 30 (Eustream, total guarantee 280,104.80), Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 120,000 kWh/h (GCA, 121,080.60) and Mosonmagyaróvár AT>HU, Day 2026-12-05, 120,000 kWh/h (GCA, "–")
- **THEN** the EUR total row shows a capacity fee of 514,056.00, a GfON fee of 58,180.80, a commodity / volume fee of 32,041.69, a capacity fee guarantee of 340,960.00, a GfON fee guarantee of 39,208.80, a commodity / volume fee guarantee of 21,016.60 and a total guarantee of 401,185.40 EUR, there is no HUF or CZK total row and no rate box, and the activation deposit note is shown under the table

#### Scenario: No day note without a GCA day row
- **WHEN** the list holds only GCA quarter rows and Eustream day rows
- **THEN** the activation deposit note is not shown

#### Scenario: EUR and HUF totals and the combined EUR total
- **WHEN** the list holds Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, booked, CEGHIX 30 (Eustream, 280,104.80 EUR) and Csanádpalota HU>RO, Quarter 2026 Q4, 100,000 kWh/h (FGSZ, 22,729,581 HUF)
- **THEN** the total table has a "Total" EUR row with a total guarantee of 280,104.80 and a "Total" HUF row with a total guarantee of 22,729,581, and a blank "HUF per 1 EUR" box is shown
- **WHEN** the box is set to "400"
- **THEN** a last row "All in EUR (1 EUR = 400 HUF)" shows a total guarantee of 336,928.75 EUR (280,104.80 + 22,729,581 / 400 = 56,823.95)
- **WHEN** the box is set to "abc"
- **THEN** the tab shows "The HUF per EUR rate must be a positive number." and the combined row is not shown

#### Scenario: No Eustream row, no Stage, CEGHIX or GfON columns
- **WHEN** the list holds only Gas Connect Austria and FGSZ rows
- **THEN** neither the list nor the total table has a Stage, CEGHIX (EUR/MWh), GfON fee or GfON fee guarantee column, and the list's columns are TSO, Network point, Product, Capacity, Surcharge (%), Currency, Capacity fee, Commodity / volume fee, Capacity fee guarantee, Commodity / volume fee guarantee, VAT, Total guarantee
- **WHEN** an Eustream booking is added to the same list
- **THEN** the four columns appear again, with "–" in the GCA and FGSZ rows

#### Scenario: EUR, HUF and CZK totals and the combined EUR total
- **WHEN** the list holds Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, booked, CEGHIX 30 (Eustream, 280,104.80 EUR), Csanádpalota HU>RO, Quarter 2026 Q4, 100,000 kWh/h (FGSZ, 22,729,581 HUF) and Lanžhot CZ>SK, Quarter 2026 Q4, 100,000 kWh/h (NET4GAS, 798,512.00 CZK)
- **THEN** the total table has "Total" rows for EUR, HUF and CZK, in that order, the CZK row with a total guarantee of 798,512.00, and blank "HUF per 1 EUR" and "CZK per 1 EUR" boxes are shown
- **WHEN** only the HUF box is set to "400"
- **THEN** the combined row is not shown
- **WHEN** the CZK box is also set to "25"
- **THEN** a last row "All in EUR (1 EUR = 400 HUF = 25 CZK)" shows a total guarantee of 368,869.23 EUR (280,104.80 + 22,729,581 / 400 + 798,512.00 / 25)
- **WHEN** the CZK box is set to "abc"
- **THEN** the tab shows "The CZK per EUR rate must be a positive number." and the combined row is not shown

## ADDED Requirements

### Requirement: NET4GAS financial security
For NET4GAS, a row's capacity fee SHALL be the total that tab 2 shows for the same point, instrument, period, capacity and unit, in CZK, raised by the row's auction surcharge and rounded to haléře once, as for the other TSOs. The guarantee SHALL be the transmission risk of Annex No. 1, section 9.i, of NET4GAS's Network Code of 7 December 2017, the value of one monthly payment:
- gas year or quarter: the largest line of the row's monthly invoice (as tab 2 shows it, raised by the surcharge);
- month or day: the whole capacity fee.

At an exit point the row SHALL also have a variable part, from NET4GAS's price calculator: the OTE index (EUR/MWh) × 0.0009 × the CZK per EUR rate × the volume in MWh at full use of the booked capacity during the whole product (the capacity in kWh/h × 24 × the product's actual days / 1000; a capacity typed in kWh/d counts as 1/24 of it in kWh/h), rounded to haléře once. The surcharge SHALL NOT change it. At an entry point the variable part SHALL be 0.

The row SHALL show the capacity fee, the variable part as the commodity / volume fee, the capacity fee guarantee and a total guarantee equal to the capacity fee guarantee: the variable part SHALL NOT be secured, as in NET4GAS's calculator, so its guarantee shows "–". The credit limit, the daily auction risk and the balancing-transmission risk SHALL NOT be included. No VAT SHALL be added.

#### Scenario: Quarter at an exit point
- **WHEN** the booking is Lanžhot CZ>SK, Quarter 2026 Q4, 100,000 kWh/h
- **THEN** the currency is CZK, the capacity fee is 2,395,536.00 and the capacity fee guarantee and total guarantee 798,512.00 (one of three equal months)

#### Scenario: Variable part as in NET4GAS's calculator
- **WHEN** the booking is Lanžhot CZ>SK, Gas year 2026/27, 480,000 kWh/d, OTE index 107.705, CZK per EUR 24.36
- **THEN** the commodity / volume fee is 413,704.04 (175,200 MWh × 107.705 × 0.0009 × 24.36), its guarantee shows "–", and the total guarantee equals the capacity fee guarantee

#### Scenario: Variable part of a quarter
- **WHEN** the booking is Lanžhot CZ>SK, Quarter 2026 Q4, 100,000 kWh/h, OTE index 107.705, CZK per EUR 24.36
- **THEN** the commodity / volume fee is 521,380.43 (220,800 MWh) and the total guarantee stays 798,512.00

#### Scenario: Gas year across a tariff change
- **WHEN** the booking is Lanžhot CZ>SK, Gas year 2026/27, 100,000 kWh/h
- **THEN** the capacity fee is 9,000,000.00 (October to December at 720,000.00, January to September at 760,000.00) and the guarantee 760,000.00

#### Scenario: Gas year with its dearest months first
- **WHEN** the booking is Lanžhot CZ>SK, Gas year 2025/26, 100,000 kWh/h
- **THEN** the capacity fee is 10,380,000.00 and the guarantee 1,300,000.00, the October to December 2025 month

#### Scenario: Month typed in kWh/d
- **WHEN** the booking is Lanžhot CZ>SK, Month 2027-01, 2,400,000 kWh/d (100,000 kWh/h)
- **THEN** the capacity fee and the guarantee are 968,208.00

#### Scenario: Day
- **WHEN** the booking is Lanžhot CZ>SK, Day 2026-12-05, 100,000 kWh/h
- **THEN** the capacity fee and the guarantee are 35,496.00

#### Scenario: Entry point
- **WHEN** the booking is Lanžhot SK>CZ, Quarter 2026 Q4, 100,000 kWh/h
- **THEN** the capacity fee is 1,146,480.00, the commodity / volume fee 0.00, and the guarantee 382,160.00, and no OTE index or rate is needed

#### Scenario: Quarter with a surcharge
- **WHEN** the booking is Lanžhot CZ>SK, Quarter 2026 Q4, 100,000 kWh/h, surcharge 10
- **THEN** the capacity fee is 2,635,089.60 and the guarantee 878,363.20

### Requirement: Description of NET4GAS's rule
When NET4GAS is the chosen TSO, the tab SHALL show, under the TSO dropdown, a closed expander "How NET4GAS calculates the financial guarantee". The description SHALL be taken from Annex No. 1 (Conditions of Financial Eligibility of the Network User) of NET4GAS's Network Code of 7 December 2017 and SHALL cover:
- how much (9): the credit exposure (the maximum possible debt less the securities provided) must stay within the credit limit; the debt is the sum of the transmission risk (the monthly payment for all contracted capacities, which the tab calculates: the most expensive month for a gas year or quarter, the whole fee for a month or day), the daily auction risk and the balancing-transmission risk (0 with an Agreement on Imbalance Settlement), the last two not included in the tab;
- the variable part at exit points: OTE index (EUR/MWh) × 0.0009 × CZK per EUR × the volume at full use, typed by the user, shown but not included in the credit exposure;
- VAT (9): counted when NET4GAS must charge Czech VAT (21%); the tab adds none because cross-border transmission for a Hungarian user is reverse-charged;
- the credit limit (8): 20%, 10% or 5% of equity by rating, 0 below BBB-, a higher limit after an extended analysis; not subtracted by the tab;
- when (3): 2 calendar months before the first gas day, or 2 business days before a booking, transfer or auction bid;
- how long (4, 5, 11): for the whole contract, at least the next 90 calendar days, up to 2 calendar months after it ends; returned within 10 business days once all liabilities are settled;
- the forms (10): bank guarantee or guarantor's guarantee from an issuer rated at least BBB- / Baa3, or a security deposit.

#### Scenario: NET4GAS description
- **WHEN** NET4GAS is the chosen TSO
- **THEN** the tab shows a closed expander "How NET4GAS calculates the financial guarantee" that mentions the monthly payment, the most expensive month, the Credit Limit, 21% VAT and 90 calendar days
