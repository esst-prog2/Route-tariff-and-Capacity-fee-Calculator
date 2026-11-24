# bank-guarantee-calculator Specification

## Purpose

Lets a trader work out the financial guarantee (bank guarantee) a TSO requires for a list of capacity bookings, for a capacity auction or for booked capacity, following each TSO's own rule, starting with Eustream.

## Requirements

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

### Requirement: Eustream capacity fee guarantee
For Eustream, a row's capacity fee SHALL be the total that tab 2 shows for the same point, instrument, period, capacity and unit, including tab 2's monthly invoice (a gas year in twelfths, a quarter in thirds, each month at the tariff valid in it), raised by the row's auction surcharge: capacity × tariff + capacity × tariff × surcharge / 100. The surcharged fee SHALL be computed exactly and rounded to cents once, and its monthly invoice SHALL be split in the same proportions as tab 2's invoice, so that it adds up to the fee (Eustream's equal thirds or twelfths stay equal). With no surcharge the fee and invoice are tab 2's. The capacity fee guarantee follows Operational Order 7.6.2:
- for a gas year or a quarter (contracts longer than two months), it SHALL be the sum of the two largest monthly invoice amounts;
- for a month or a day, it SHALL be the whole capacity fee.

This applies in both stages, and the guarantee is taken from the surcharged fee. The surcharge SHALL NOT change the GfON.

#### Scenario: Quarter
- **WHEN** the booking is Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h (Q4_Oct 3.61344 EUR per kWh/h)
- **THEN** the capacity fee is 361,344.00 EUR (three invoices of 120,448.00) and the capacity fee guarantee is 240,896.00 EUR

#### Scenario: Gas year across a tariff change
- **WHEN** the booking is Balassagyarmat SK>HU, Gas year 2025/26, 10,000 kWh/h (Year 8.76 until April 2026, 9.636 from 1 May 2026)
- **THEN** the capacity fee is 91,250.00 EUR (seven invoices of 7,300.00 and five of 8,030.00) and the capacity fee guarantee is 16,060.00 EUR (two months at 8,030.00)

#### Scenario: Month typed in kWh/d
- **WHEN** the booking is Balassagyarmat SK>HU, Month 2027-01, 2,400,000 kWh/d (100,000 kWh/h at M_Jan 1.20456)
- **THEN** the capacity fee and the capacity fee guarantee are both 120,456.00 EUR

#### Scenario: Day at auction
- **WHEN** the booking is Balassagyarmat SK>HU, Day 2026-12-05, 100,000 kWh/h (D_Dec 0.07896), stage "Capacity auction"
- **THEN** the capacity fee and capacity fee guarantee are 7,896.00 EUR, CEGHIX, GfON fee and GfON fee guarantee show "–", and the total guarantee is 7,896.00 EUR

#### Scenario: Quarter with a surcharge
- **WHEN** the booking is Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, surcharge 10, stage "Booked capacity", CEGHIX 30
- **THEN** the capacity fee is 397,478.40 EUR (three invoices of 132,492.80), the capacity fee guarantee is 264,985.60 EUR, the GfON fee and GfON fee guarantee are unchanged (58,180.80 and 39,208.80 EUR), and the total guarantee is 304,194.40 EUR

#### Scenario: Day at auction with a surcharge
- **WHEN** the booking is Balassagyarmat SK>HU, Day 2026-12-05, 100,000 kWh/h, surcharge "2,5", stage "Capacity auction"
- **THEN** the surcharge column shows "2.5" and the capacity fee, capacity fee guarantee and total guarantee are 8,093.40 EUR

### Requirement: Eustream GfON fee and guarantee
For an Eustream "Booked capacity" row, the GfON fee (Eustream's neutrality fee) SHALL be computed as follows:
- The volume is the transported volume at full use of the booked capacity during the product, in MWh: the capacity in kWh/h × 24 × the product's days / 1000. A capacity typed in kWh/d counts as 1/24 of it in kWh/h. Every gas day counts as 24 hours, including the days when the clock changes.
- The GfON rate in EUR/MWh is (CEGHIX + 1) × 0.85 / 100, unrounded.
- The GfON fee is the volume × the rate, rounded to cents (halves up).

The GfON fee guarantee follows Operational Order 7.6.2:
- for a gas year or a quarter, it SHALL be the GfON of the two calendar months of the product with the largest volume (the months with the most days), rounded to cents;
- for a month or a day, it SHALL equal the GfON fee.

The total guarantee SHALL be the capacity fee guarantee plus the GfON fee guarantee. Amounts SHALL be computed with exact decimals, not binary floating point.

#### Scenario: Quarter, booked
- **WHEN** the booking is Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, stage "Booked capacity", CEGHIX 30
- **THEN** the GfON rate is 0.2635 EUR/MWh, the volume is 220,800 MWh, the GfON fee is 58,180.80 EUR, the GfON fee guarantee is 39,208.80 EUR (October and December, 148,800 MWh), and the total guarantee is 280,104.80 EUR

#### Scenario: Same quarter at auction
- **WHEN** the same booking is added with stage "Capacity auction"
- **THEN** the total guarantee is 240,896.00 EUR

#### Scenario: Gas year, booked
- **WHEN** the booking is Balassagyarmat SK>HU, Gas year 2025/26, 10,000 kWh/h, stage "Booked capacity", CEGHIX 40
- **THEN** the GfON rate is 0.3485 EUR/MWh, the GfON fee is 30,528.60 EUR (87,600 MWh), the GfON fee guarantee is 5,185.68 EUR (two 31-day months, 14,880 MWh), and the total guarantee is 21,245.68 EUR

#### Scenario: Month, booked
- **WHEN** the booking is Balassagyarmat SK>HU, Month 2027-01, 2,400,000 kWh/d, stage "Booked capacity", CEGHIX 30
- **THEN** the GfON fee and GfON fee guarantee are both 19,604.40 EUR (74,400 MWh), and the total guarantee is 140,060.40 EUR

### Requirement: Description of the TSO's rule
When a TSO with a description is chosen, the tab SHALL show, under the TSO dropdown, a closed expander "How <TSO> calculates the financial guarantee" with the TSO's rule in words. For Eustream the description SHALL be taken from the English Operational Order valid from 24 July 2025 (sections 3.3.1, 4.2.12 and 7.6), SHALL say that the Slovak version is binding, and SHALL cover:
- how much: the capacity fee and the GfON separately; two months' payment for a gas year or quarter, the whole payment for a month or day; at a capacity auction only the capacity fee, including the surcharge; the daily GfON formula;
- when it is due: capacity is allocated only once the guarantee is in place; at points to and from third countries and the domestic point, within 15 calendar days of the request for annual and longer contracts, 7 for short-term ones, and at least 3 business days before transmission starts;
- how long it is held: an irrevocable bank guarantee expiring no earlier than two months after the end of the contract, kept at the required level for the whole contract and topped up within 3 calendar days after a draw;
- the accepted forms: bank guarantee, pre-payment or cash collateral, noting that Eustream may set another amount after a credit check (7.6.5) or reassess it (7.6.4), and that the imbalance guarantee (7.6.3) is not covered.

#### Scenario: Eustream description
- **WHEN** Eustream is the chosen TSO
- **THEN** the tab shows a closed expander "How Eustream calculates the financial guarantee" that mentions two months' payment, a bank guarantee expiring no earlier than two months after the contract, and the 3 calendar days to top it up

### Requirement: Gas Connect Austria security deposit
For Gas Connect Austria, a row's capacity fee SHALL be computed as for Eustream: the total that tab 2 shows for the same point, instrument, period, capacity and unit, including tab 2's monthly invoice (a gas year in twelfths, a quarter in thirds, each month at the tariff valid in it), raised by the row's auction surcharge, rounded to cents once, with the invoice split in the same proportions as tab 2's. The capacity fee guarantee follows GTC chapter IV para. 15 (version of 23 September 2013):
- for a month, it SHALL be the whole capacity fee;
- for a quarter, it SHALL be the sum of the first two monthly invoice amounts;
- for a gas year, it SHALL be the sum of the first three monthly invoice amounts;
- for a day, there SHALL be no capacity fee guarantee (shown as "–", counted as zero).

A GCA row SHALL also carry GCA's commodity charge:
- The volume is the transported volume at full use of the booked capacity, in MWh: the capacity in kWh/h × 24 × days / 1000 (a capacity typed in kWh/d counts as 1/24 of it in kWh/h; every gas day counts as 24 hours). For example, 150,000 kWh/h in December 2026 at an exit point is 150,000 × 24 × 31 / 1000 = 111,600 MWh × 0.11963 = 13,350.71 EUR.
- The rate in EUR/MWh depends on the point's direction (entry or exit, virtual points included) and on the date: from 1 January 2026, 0.03322 at entry and 0.11963 at exit; from 1 January 2027, 0.07914 at entry and 0.2586 at exit. Before 1 January 2026 the commodity charge SHALL count as 0.
- The commodity fee is the commodity charge for the whole product; the commodity fee guarantee is the commodity charge for the months the capacity fee guarantee covers (the whole month; the first two months of a quarter; the first three of a gas year). For a day the commodity fee is shown and the commodity fee guarantee is "–".
- Each is computed exactly and rounded to cents once (halves up). The auction surcharge SHALL NOT change the commodity charge.

A GCA row SHALL have no GfON fee or GfON fee guarantee, and its total guarantee SHALL be its capacity fee guarantee plus its commodity fee guarantee. The EUR 100,000 activation deposit SHALL NOT be added to any row or total. Amounts SHALL be computed with exact decimals, not binary floating point.

#### Scenario: Quarter
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 120,000 kWh/h (Q4_Oct 1.25082191, billed as 1.2508 EUR per kWh/h)
- **THEN** the capacity fee is 150,096.00 EUR (three invoices of 50,032.00) and the capacity fee guarantee 100,064.00 EUR; the commodity fee is 31,697.16 EUR (264,960 MWh at 0.11963) and the commodity fee guarantee 21,016.60 EUR (October and November, 175,680 MWh); the total guarantee is 121,080.60 EUR; Stage, CEGHIX, GfON fee and GfON fee guarantee show "–"

#### Scenario: Gas year across a tariff change
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Gas year 2025/26, 120,000 kWh/h (Year 2.14 in 2025, 3.97 from 1 January 2026)
- **THEN** the capacity fee is 421,500.00 EUR (three invoices of 21,400.00 and nine of 39,700.00) and the capacity fee guarantee is 64,200.00 EUR (October to December), not the two most expensive months; the commodity fee is 94,057.89 EUR (January to September 2026 only, 786,240 MWh at 0.11963), the commodity fee guarantee is 0.00 EUR (October to December 2025 have no rate), and the total guarantee is 64,200.00 EUR

#### Scenario: Gas year across a commodity rate change
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Gas year 2026/27, 120,000 kWh/h
- **THEN** the capacity fee guarantee is 119,100.00 EUR, the commodity fee is 235,018.83 EUR (October to December 2026 at 0.11963, January to September 2027 at 0.2586), the commodity fee guarantee is 31,697.16 EUR (October to December 2026) and the total guarantee is 150,797.16 EUR

#### Scenario: Month typed in kWh/d
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Month 2027-01, 2,880,000 kWh/d (120,000 kWh/h, M_Jan 0.52232877 billed as 0.5223)
- **THEN** the capacity fee and the capacity fee guarantee are 62,676.00 EUR, the commodity fee and commodity fee guarantee are 23,087.81 EUR (89,280 MWh at 0.2586), and the total guarantee is 85,763.81 EUR

#### Scenario: The user's December example
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Month 2026-12, 150,000 kWh/h
- **THEN** the commodity fee and commodity fee guarantee are 13,350.71 EUR

#### Scenario: Entry point
- **WHEN** the booking is VIP Oberkappel DE>AT, Quarter 2027 Q1, 120,000 kWh/h
- **THEN** the commodity fee is 20,513.09 EUR (259,200 MWh at the entry rate 0.07914) and the commodity fee guarantee is 13,447.47 EUR (January and February, 169,920 MWh)

#### Scenario: Day
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Day 2026-12-05, 120,000 kWh/h (D_Dec 0.02175342 billed as 0.0218)
- **THEN** the capacity fee is 2,616.00 EUR, the commodity fee is 344.53 EUR (2,880 MWh), and the capacity fee guarantee, commodity fee guarantee and total guarantee show "–"

#### Scenario: Quarter with a surcharge
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 120,000 kWh/h, surcharge 10
- **THEN** the capacity fee is 165,105.60 EUR (three invoices of 55,035.20) and the capacity fee guarantee 110,070.40 EUR; the commodity fee (31,697.16) and commodity fee guarantee (21,016.60) are as without a surcharge; the total guarantee is 131,087.00 EUR

#### Scenario: Day with a surcharge
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Day 2026-12-05, 120,000 kWh/h, surcharge "2,5"
- **THEN** the capacity fee is 2,681.40 EUR, the commodity fee 344.53 EUR, and the capacity fee guarantee and total guarantee show "–"

### Requirement: Description of Gas Connect Austria's rule
When Gas Connect Austria is the chosen TSO, the tab SHALL show, under the TSO dropdown, a closed expander "How Gas Connect Austria calculates the financial guarantee". The description SHALL be taken from chapter IV of GCA's General Terms and Conditions for Transmission Network Access (Annex 1 to the Frame Capacity Contract, version of 23 September 2013), SHALL say that the German version is binding, and SHALL cover:
- how much (IV.15): the whole fee for a month, the fee of the first two months for a quarter, of the first three months for a gas year, including the auction surcharge and excluding the bank fees; no security deposit for a day, which the activation deposit covers;
- the commodity charge added to it: the volume of the same months at full use of the capacity, times the rates from 1 January 2026 (entry 0.03322, exit 0.11963 EUR/MWh) and from 1 January 2027 (entry 0.07914, exit 0.2586 EUR/MWh), counted as 0 before 1 January 2026;
- the activation deposit (IV.6–10): a one-off EUR 100,000 bank guarantee (unlimited in time, on GCA's sample) or cash deposit, due at least 5 working days before the first auction and after each draw, kept at the full amount, covering contracts of one day or less; GCA may adjust the amount; it is not included in the tab's totals;
- when (IV.13–14): the security deposit is due no later than 5 working days after the capacity contract is concluded;
- how long (IV.13–14): the bank guarantee is returned, and the cash deposit repaid without interest, once all obligations under the capacity contract are met;
- if missed (IV.16): GCA may claim the activation deposit, the capacity contract ends at once, and the user may not take part in auctions until it has paid in full;
- the forms: bank guarantee (on GCA's sample) or cash deposit, at the user's choice.

#### Scenario: GCA description
- **WHEN** Gas Connect Austria is the chosen TSO
- **THEN** the tab shows a closed expander "How Gas Connect Austria calculates the financial guarantee" that mentions the first two months for a quarter, the first three months for a gas year, the commodity charge with its four rates, the EUR 100,000 activation deposit and the 5 working days after the contract is concluded

### Requirement: FGSZ contractual security
For FGSZ, a row's capacity fee (K+A) SHALL be the total that tab 2 shows for the same point, instrument, period, capacity and unit, in HUF, raised by the row's auction surcharge and rounded to whole forints once, as for the other TSOs. The guarantee SHALL be the contractual security of GTC 4.d section 7.5 (applicable as of 1 October 2026):
- gas year: ((K+A) × 1/12 + 2 × F × 1/12 × k) × (1 + VAT);
- quarter: ((K+A) × 1/3 + 2 × F × 1/3 × k) × (1 + VAT);
- month or day: (K+A + F × k) × (1 + VAT);

where:
- F, the volume fee, is the transported volume at full use of the booked capacity during the whole product, in MWh (the capacity in kWh/h × 24 × days / 1000; a capacity typed in kWh/d counts as 1/24 of it in kWh/h; every gas day counts as 24 hours), times 29.22 HUF/MWh at exit points; at entry points F SHALL be 0. There SHALL be no odourisation fee;
- k, the correction multiplier, is 80.05%;
- VAT is always 27%.

The same volume fee, k and VAT SHALL apply on every date, also before 1 October 2026. The 1/12, 2/12, 1/3 and 2/3 shares SHALL be applied exactly to the product's fee and volume fee, not taken from particular monthly invoices.

The row SHALL show:
- Capacity fee: K+A;
- Commodity / volume fee: F, rounded to whole forints;
- Capacity fee guarantee: the capacity part, (K+A) × the share, rounded to whole forints (halves away from zero);
- Commodity / volume fee guarantee: the volume part, F × the double share × k (or F × k for a month or day), rounded to whole forints;
- VAT: 27% of the capacity fee guarantee plus the commodity / volume fee guarantee, rounded to whole forints;
- Total guarantee: the capacity fee guarantee + the commodity / volume fee guarantee + the VAT.

The surcharge SHALL NOT change F. Amounts SHALL be computed with exact decimals, not binary floating point.

#### Scenario: Quarter at an exit point
- **WHEN** the booking is Csanádpalota HU>RO, Quarter 2026 Q4, 100,000 kWh/h
- **THEN** the currency is HUF, the capacity fee is 43,362,631, the commodity / volume fee 6,451,776 (220,800 MWh × 29.22), the capacity fee guarantee 14,454,210, the commodity / volume fee guarantee 3,443,098, the VAT 4,832,273 and the total guarantee 22,729,581; Stage, CEGHIX, GfON fee and GfON fee guarantee show "–"

#### Scenario: Gas year at an exit point
- **WHEN** the booking is Csanádpalota HU>RO, Gas year 2026/27, 100,000 kWh/h
- **THEN** the capacity fee is 132,648,000, the commodity / volume fee 25,596,720 (876,000 MWh), the capacity fee guarantee 11,054,000, the commodity / volume fee guarantee 3,415,029, the VAT 3,906,638 and the total guarantee 18,375,667 HUF

#### Scenario: Gas year before 1 October 2026
- **WHEN** the booking is Csanádpalota HU>RO, Gas year 2025/26, 100,000 kWh/h
- **THEN** the same volume fee and k are used: the capacity fee is 132,727,000, the capacity fee guarantee 11,060,583 (exactly 1/12, not the 11,060,584 of the first invoice), the commodity / volume fee guarantee 3,415,029, the VAT 3,908,415 and the total guarantee 18,384,027 HUF

#### Scenario: Month typed in kWh/d
- **WHEN** the booking is Csanádpalota HU>RO, Month 2027-01, 2,400,000 kWh/d (100,000 kWh/h)
- **THEN** the capacity fee and the capacity fee guarantee are 19,074,782, the commodity / volume fee is 2,173,968 (74,400 MWh), the commodity / volume fee guarantee 1,740,261, the VAT 5,620,062 and the total guarantee 26,435,105 HUF

#### Scenario: Day
- **WHEN** the booking is Csanádpalota HU>RO, Day 2026-12-05, 100,000 kWh/h
- **THEN** the capacity fee and the capacity fee guarantee are 1,047,919, the commodity / volume fee is 70,128 (2,400 MWh), the commodity / volume fee guarantee 56,137, the VAT 298,095 and the total guarantee 1,402,151 HUF

#### Scenario: Entry point has no volume fee
- **WHEN** the booking is Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 100,000 kWh/h
- **THEN** the capacity fee is 37,562,771, the commodity / volume fee and its guarantee are 0, the capacity fee guarantee 12,520,924, the VAT 3,380,649 and the total guarantee 15,901,573 HUF

#### Scenario: Quarter with a surcharge
- **WHEN** the booking is Csanádpalota HU>RO, Quarter 2026 Q4, 100,000 kWh/h, surcharge 10
- **THEN** the capacity fee is 47,698,894, the capacity fee guarantee 15,899,631, the commodity / volume fee guarantee is unchanged at 3,443,098, the VAT 5,222,537 and the total guarantee 24,565,266 HUF

### Requirement: Description of FGSZ's rule
When FGSZ is the chosen TSO, the tab SHALL show, under the TSO dropdown, a closed expander "How FGSZ calculates the financial guarantee". The description SHALL be taken from chapter 7 of FGSZ's General Terms and Conditions for Network Usage Contracts (GTC 4.d, applicable as of 1 October 2026) and SHALL cover:
- how much (7.5): the contractual security formula for a gas year, a quarter, and a month or day in words, with the volume fee of 29.22 HUF/MWh at exit points, k = 80.05% and 27% VAT, and that the auction surcharge is the auction fee A;
- the fixed amounts, not included in the tab's totals: the minimum guarantee of HUF 10,000,000 for the framework contract (7.2) and the auction security of at least HUF 35,000,000 for long-term and quarterly auctions (7.4.1);
- the risk classes (7.4.1): low, medium and high, with their locking multipliers (long-term 0.05, 0.0833 and 0.5; quarterly 0.2, 0.33 and 1), and that a high-risk user also has 5/12 of the annual capacity and auction fee (long-term) or 2/3 of the quarterly fee for the next two quarters locked as additional security; none of this is included in the tab;
- when and how long (7.4, 7.5): the auction security is due by 12:00 on the banking day before the auction; the contractual security must be in effect by the first day of the service period and remain valid at least 60 days after it;
- the forms (7.1): bank guarantee from a bank rated at least BB (S&P, or the Moody's or Fitch equivalent), or cash deposit without interest;
- that additional security (7.3) is requested case by case and is not covered.

#### Scenario: FGSZ description
- **WHEN** FGSZ is the chosen TSO
- **THEN** the tab shows a closed expander "How FGSZ calculates the financial guarantee" that mentions the 1/12 and 1/3 shares, 29.22 HUF/MWh, 80.05%, 27% VAT, HUF 10,000,000, HUF 35,000,000 and 60 days after the service period

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
