## MODIFIED Requirements

### Requirement: Booking inputs
The app SHALL have a third tab, "Bank Guarantee Calculator", after the Route Tariff Calculator and the Capacity Fee Calculator. The tab SHALL take:
- a TSO from a dropdown that offers Eustream and then Gas Connect Austria, starting on Eustream;
- a network point from a dropdown of that TSO's single sides, labelled as on tab 2;
- a product instrument (gas year, quarter, month or day) and its period, with the same pickers, choices and defaults as tab 2;
- a requested capacity with its unit (kWh/h, the default, or kWh/d), as on tab 2;
- for Eustream only, a stage: "Capacity auction" or "Booked capacity" (the default);
- an "Auction surcharge (%)" box, for both TSOs and at either stage, that starts blank and carries the note "The auction surcharge (premium) in %, added to the tariff; leave it blank for none." A blank box means 0%; a decimal comma is accepted.

For Eustream at "Booked capacity" the tab SHALL also take the CEGHIX in EUR/MWh, in a box that starts blank and carries the note "Enter the CEGHIX valid on the day before the booking." For Eustream at "Capacity auction" the CEGHIX box SHALL NOT be shown. For Gas Connect Austria neither the stage nor the CEGHIX box SHALL be shown.

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
- **THEN** the choices are Eustream and Gas Connect Austria, in that order, and Eustream is chosen

#### Scenario: Only Eustream is offered
- **WHEN** Eustream is the chosen TSO and the user opens the network point dropdown
- **THEN** it lists only Eustream's single sides (for example "Balassagyarmat SK>HU (21Z000000000358C)"), no GCA point

#### Scenario: GCA inputs
- **WHEN** the user chooses Gas Connect Austria
- **THEN** the network point dropdown lists GCA's single sides as on tab 2 (for example "Mosonmagyaróvár AT>HU (21Z000000000003C)"), the "Auction surcharge (%)" box is shown, and neither the stage nor the CEGHIX box is shown

### Requirement: List of bookings
An "Add to list" button SHALL add the booking to a list shown as a table. Each row SHALL keep the TSO, surcharge and, for Eustream, the stage and CEGHIX it was added with. A booking SHALL NOT be added, and a message SHALL be shown instead, in these cases:
- the capacity is invalid: tab 2's message "Capacity must be a positive number.";
- the period has no tariff: tab 2's no-tariff message;
- the surcharge is negative or not a number: "The surcharge must be a percentage of 0 or more.";
- for Eustream at "Booked capacity", the CEGHIX is blank, zero, negative or not a number: "CEGHIX must be a positive number."

Adding the same booking more than once SHALL be allowed. Rows of both TSOs SHALL be allowed in the same list. Rows SHALL be selectable and removed with "Remove selected rows". "Clear list" SHALL empty the list. An empty list SHALL show "Add a booking to start the list." The list SHALL last for the browser session.

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

### Requirement: Table columns and total
Each row SHALL show these columns, in this order:
- TSO;
- Network point, as name and flow, e.g. "Balassagyarmat SK>HU";
- Product: the instrument and period, e.g. "Quarter 2026 Q4", "Gas year 2025/26", "Month 2027-01", "Day 2026-12-05";
- Capacity, as typed with its unit, with thousands separators, e.g. "100,000 kWh/h";
- Stage;
- Surcharge (%), as typed, e.g. "10" or "2.5", or "–" when there is none (blank or 0);
- CEGHIX (EUR/MWh);
- Capacity fee;
- GfON fee;
- Commodity fee;
- Capacity fee guarantee;
- GfON fee guarantee;
- Commodity fee guarantee;
- Total guarantee.

All amounts SHALL be in EUR with two decimals and thousands separators. For an Eustream row, the Commodity fee and Commodity fee guarantee cells SHALL show "–". For an Eustream "Capacity auction" row, the CEGHIX, GfON fee and GfON fee guarantee cells SHALL also show "–", and the total guarantee SHALL equal the capacity fee guarantee. For a Gas Connect Austria row, the Stage, CEGHIX, GfON fee and GfON fee guarantee cells SHALL show "–", and the total guarantee SHALL equal the capacity fee guarantee plus the commodity fee guarantee; for a GCA day row the capacity fee guarantee, commodity fee guarantee and total guarantee cells SHALL also show "–". A total row under the table SHALL add up the capacity fee, GfON fee, commodity fee, capacity fee guarantee, GfON fee guarantee, commodity fee guarantee and total guarantee of all rows, counting "–" as zero.

When the list holds at least one Gas Connect Austria day row, the tab SHALL show under the table the note "Gas Connect Austria asks no security deposit for day contracts: they are covered by its one-off activation deposit of EUR 100,000, which is not included in the total."

#### Scenario: Total of a mixed list
- **WHEN** the list holds the Balassagyarmat SK>HU rows of the scenarios below: 2026 Q4 booked (total guarantee 280,104.80), January 2027 booked (140,060.40) and 5 December 2026 at auction (7,896.00)
- **THEN** the total row's total guarantee is 428,061.20 EUR

#### Scenario: Total of a list with both TSOs
- **WHEN** the list holds Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, booked, CEGHIX 30 (Eustream, total guarantee 280,104.80), Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 120,000 kWh/h (GCA, 121,080.60) and Mosonmagyaróvár AT>HU, Day 2026-12-05, 120,000 kWh/h (GCA, "–")
- **THEN** the total row shows a capacity fee of 514,056.00, a GfON fee of 58,180.80, a commodity fee of 32,041.69, a capacity fee guarantee of 340,960.00, a GfON fee guarantee of 39,208.80, a commodity fee guarantee of 21,016.60 and a total guarantee of 401,185.40 EUR, and the activation deposit note is shown under the table

#### Scenario: No day note without a GCA day row
- **WHEN** the list holds only GCA quarter rows and Eustream day rows
- **THEN** the activation deposit note is not shown

## ADDED Requirements

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
