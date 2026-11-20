## MODIFIED Requirements

### Requirement: Booking inputs
The app SHALL have a third tab, "Bank Guarantee Calculator", after the Route Tariff Calculator and the Capacity Fee Calculator. The tab SHALL take:
- a TSO from a dropdown that offers Eustream, Gas Connect Austria and then FGSZ, starting on Eustream;
- a network point from a dropdown of that TSO's single sides, labelled as on tab 2;
- a product instrument (gas year, quarter, month or day) and its period, with the same pickers, choices and defaults as tab 2;
- a requested capacity with its unit (kWh/h, the default, or kWh/d), as on tab 2;
- for Eustream only, a stage: "Capacity auction" or "Booked capacity" (the default);
- an "Auction surcharge (%)" box, for every TSO and at either stage, that starts blank and carries the note "The auction surcharge (premium) in %, added to the tariff; leave it blank for none." A blank box means 0%; a decimal comma is accepted.

For Eustream at "Booked capacity" the tab SHALL also take the CEGHIX in EUR/MWh, in a box that starts blank and carries the note "Enter the CEGHIX valid on the day before the booking." For Eustream at "Capacity auction" the CEGHIX box SHALL NOT be shown. For Gas Connect Austria and FGSZ neither the stage nor the CEGHIX box SHALL be shown. FGSZ SHALL have no VAT input.

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
- **THEN** the choices are Eustream, Gas Connect Austria and FGSZ, in that order, and Eustream is chosen

#### Scenario: Only Eustream is offered
- **WHEN** Eustream is the chosen TSO and the user opens the network point dropdown
- **THEN** it lists only Eustream's single sides (for example "Balassagyarmat SK>HU (21Z000000000358C)"), no GCA or FGSZ point

#### Scenario: GCA inputs
- **WHEN** the user chooses Gas Connect Austria
- **THEN** the network point dropdown lists GCA's single sides as on tab 2 (for example "Mosonmagyaróvár AT>HU (21Z000000000003C)"), the "Auction surcharge (%)" box is shown, and neither the stage nor the CEGHIX box is shown

#### Scenario: FGSZ inputs
- **WHEN** the user chooses FGSZ
- **THEN** the network point dropdown lists FGSZ's 14 single sides as on tab 2 (for example "Csanádpalota HU>RO (21Z000000000236Q)" and "Mosonmagyaróvár AT>HU (21Z000000000003C)"), the "Auction surcharge (%)" box is shown, and no stage, CEGHIX or VAT input is shown

### Requirement: List of bookings
An "Add to list" button SHALL add the booking to a list shown as a table. Each row SHALL keep the TSO, surcharge and, for Eustream, the stage and CEGHIX it was added with. A booking SHALL NOT be added, and a message SHALL be shown instead, in these cases:
- the capacity is invalid: tab 2's message "Capacity must be a positive number.";
- the period has no tariff: tab 2's no-tariff message;
- the surcharge is negative or not a number: "The surcharge must be a percentage of 0 or more.";
- for Eustream at "Booked capacity", the CEGHIX is blank, zero, negative or not a number: "CEGHIX must be a positive number."

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

### Requirement: Table columns and total
Each row SHALL show these columns, in this order:
- TSO;
- Network point, as name and flow, e.g. "Balassagyarmat SK>HU";
- Product: the instrument and period, e.g. "Quarter 2026 Q4", "Gas year 2025/26", "Month 2027-01", "Day 2026-12-05";
- Capacity, as typed with its unit, with thousands separators, e.g. "100,000 kWh/h";
- Stage;
- Surcharge (%), as typed, e.g. "10" or "2.5", or "–" when there is none (blank or 0);
- CEGHIX (EUR/MWh);
- Currency: EUR for Eustream and Gas Connect Austria, HUF for FGSZ;
- Capacity fee;
- GfON fee;
- Commodity / volume fee;
- Capacity fee guarantee;
- GfON fee guarantee;
- Commodity / volume fee guarantee;
- VAT;
- Total guarantee.

Every amount SHALL be in the row's currency with thousands separators: EUR with two decimals, HUF in whole forints. For an Eustream row, the Commodity / volume fee, Commodity / volume fee guarantee and VAT cells SHALL show "–". For an Eustream "Capacity auction" row, the CEGHIX, GfON fee and GfON fee guarantee cells SHALL also show "–", and the total guarantee SHALL equal the capacity fee guarantee. For a Gas Connect Austria row, the Stage, CEGHIX, GfON fee, GfON fee guarantee and VAT cells SHALL show "–", and the total guarantee SHALL equal the capacity fee guarantee plus the commodity / volume fee guarantee; for a GCA day row the capacity fee guarantee, commodity / volume fee guarantee and total guarantee cells SHALL also show "–". For an FGSZ row, the Stage, CEGHIX, GfON fee and GfON fee guarantee cells SHALL show "–", and the total guarantee SHALL equal the capacity fee guarantee plus the commodity / volume fee guarantee plus the VAT.

A total table under the list SHALL have one row per currency present in the list, EUR first and then HUF, labelled "Total" with that currency in its Currency column; each SHALL add up every amount column of the list's rows in that currency, counting "–" as zero.

When the list holds at least one HUF row, the tab SHALL show under the total table a "HUF per 1 EUR" box that starts blank. When it holds a positive number (a decimal comma is accepted), the total table SHALL end with a row "All in EUR (1 EUR = <rate> HUF)", with EUR as its currency, in which each amount column is the EUR total plus the HUF total divided by the rate, rounded to cents. When the box is blank the row SHALL NOT be shown; when it holds anything else the tab SHALL show "The HUF per EUR rate must be a positive number." and SHALL NOT show the row.

When the list holds at least one Gas Connect Austria day row, the tab SHALL show under the table the note "Gas Connect Austria asks no security deposit for day contracts: they are covered by its one-off activation deposit of EUR 100,000, which is not included in the total."

#### Scenario: Total of a mixed list
- **WHEN** the list holds the Balassagyarmat SK>HU rows of the scenarios below: 2026 Q4 booked (total guarantee 280,104.80), January 2027 booked (140,060.40) and 5 December 2026 at auction (7,896.00)
- **THEN** the total row's total guarantee is 428,061.20 EUR

#### Scenario: Total of a list with both TSOs
- **WHEN** the list holds Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, booked, CEGHIX 30 (Eustream, total guarantee 280,104.80), Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 120,000 kWh/h (GCA, 121,080.60) and Mosonmagyaróvár AT>HU, Day 2026-12-05, 120,000 kWh/h (GCA, "–")
- **THEN** the EUR total row shows a capacity fee of 514,056.00, a GfON fee of 58,180.80, a commodity / volume fee of 32,041.69, a capacity fee guarantee of 340,960.00, a GfON fee guarantee of 39,208.80, a commodity / volume fee guarantee of 21,016.60 and a total guarantee of 401,185.40 EUR, there is no HUF total row and no "HUF per 1 EUR" box, and the activation deposit note is shown under the table

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

## ADDED Requirements

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
