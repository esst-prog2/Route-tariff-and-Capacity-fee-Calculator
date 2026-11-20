## MODIFIED Requirements

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

The Stage, CEGHIX (EUR/MWh), GfON fee and GfON fee guarantee columns SHALL be shown only when the list holds at least one Eustream row; otherwise they SHALL be left out of both the list and the total table, and the other columns keep their order.

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

#### Scenario: No Eustream row, no Stage, CEGHIX or GfON columns
- **WHEN** the list holds only Gas Connect Austria and FGSZ rows
- **THEN** neither the list nor the total table has a Stage, CEGHIX (EUR/MWh), GfON fee or GfON fee guarantee column, and the list's columns are TSO, Network point, Product, Capacity, Surcharge (%), Currency, Capacity fee, Commodity / volume fee, Capacity fee guarantee, Commodity / volume fee guarantee, VAT, Total guarantee
- **WHEN** an Eustream booking is added to the same list
- **THEN** the four columns appear again, with "–" in the GCA and FGSZ rows
