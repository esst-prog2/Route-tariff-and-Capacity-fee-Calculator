# bank-guarantee-calculator Specification

## Purpose

Lets a trader work out the financial guarantee (bank guarantee) a TSO requires for a list of capacity bookings, for a capacity auction or for booked capacity, following each TSO's own rule, starting with Eustream.

## Requirements

### Requirement: Booking inputs
The app SHALL have a third tab, "Bank Guarantee Calculator", after the Route Tariff Calculator and the Capacity Fee Calculator. The tab SHALL take:
- a TSO from a dropdown that offers only Eustream;
- a network point from a dropdown of that TSO's single sides, labelled as on tab 2;
- a product instrument (gas year, quarter, month or day) and its period, with the same pickers, choices and defaults as tab 2;
- a requested capacity with its unit (kWh/h, the default, or kWh/d), as on tab 2;
- a stage: "Capacity auction" or "Booked capacity" (the default).

For "Booked capacity" the tab SHALL also take the CEGHIX in EUR/MWh, in a box that starts blank and carries the note "Enter the CEGHIX valid on the day before the booking." For "Capacity auction" the CEGHIX box SHALL NOT be shown.

#### Scenario: CEGHIX box only for booked capacity
- **WHEN** the stage is "Booked capacity"
- **THEN** the tab shows the CEGHIX box with the note "Enter the CEGHIX valid on the day before the booking."
- **WHEN** the stage is switched to "Capacity auction"
- **THEN** the CEGHIX box is not shown

#### Scenario: Only Eustream is offered
- **WHEN** the user opens the TSO dropdown
- **THEN** the only choice is Eustream, and the network point dropdown lists Eustream's single sides (for example "Balassagyarmat SK>HU (21Z000000000358C)")

### Requirement: List of bookings
An "Add to list" button SHALL add the booking to a list shown as a table. Each row SHALL keep the stage and CEGHIX it was added with. A booking SHALL NOT be added, and a message SHALL be shown instead, in these cases:
- the capacity is invalid: tab 2's message "Capacity must be a positive number.";
- the period has no tariff: tab 2's no-tariff message;
- for "Booked capacity", the CEGHIX is blank, zero, negative or not a number: "CEGHIX must be a positive number."

Adding the same booking more than once SHALL be allowed. Rows SHALL be selectable and removed with "Remove selected rows". "Clear list" SHALL empty the list. An empty list SHALL show "Add a booking to start the list." The list SHALL last for the browser session.

#### Scenario: Adding and clearing
- **WHEN** the user adds two valid bookings and then presses "Clear list"
- **THEN** the table first shows two rows, and afterwards "Add a booking to start the list."

#### Scenario: Missing CEGHIX
- **WHEN** the stage is "Booked capacity", the CEGHIX box is blank and the user presses "Add to list"
- **THEN** the tab shows "CEGHIX must be a positive number." and the list is unchanged

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
- CEGHIX (EUR/MWh);
- Capacity fee;
- GfON fee;
- Capacity fee guarantee;
- GfON fee guarantee;
- Total guarantee.

All amounts SHALL be in EUR with two decimals and thousands separators. For a "Capacity auction" row, the CEGHIX, GfON fee and GfON fee guarantee cells SHALL show "–", and the total guarantee SHALL equal the capacity fee guarantee. A total row under the table SHALL add up the capacity fee, GfON fee, capacity fee guarantee, GfON fee guarantee and total guarantee of all rows, counting "–" as zero.

#### Scenario: Total of a mixed list
- **WHEN** the list holds the Balassagyarmat SK>HU rows of the scenarios below: 2026 Q4 booked (total guarantee 280,104.80), January 2027 booked (140,060.40) and 5 December 2026 at auction (7,896.00)
- **THEN** the total row's total guarantee is 428,061.20 EUR

### Requirement: Eustream capacity fee guarantee
For Eustream, a row's capacity fee SHALL be the total that tab 2 shows for the same point, instrument, period, capacity and unit, including tab 2's monthly invoice (a gas year in twelfths, a quarter in thirds, each month at the tariff valid in it). The capacity fee guarantee follows Operational Order 7.6.2:
- for a gas year or a quarter (contracts longer than two months), it SHALL be the sum of the two largest monthly invoice amounts;
- for a month or a day, it SHALL be the whole capacity fee.

This applies in both stages.

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
