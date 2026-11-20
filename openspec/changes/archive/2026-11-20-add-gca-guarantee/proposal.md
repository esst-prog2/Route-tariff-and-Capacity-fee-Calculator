## Why

Tab 3 (Bank Guarantee Calculator) only knows Eustream, but a route into Hungary from Austria also needs capacity at Gas Connect Austria (GCA), which asks for its own security deposit. GCA's rule, in chapter IV of its General Terms and Conditions for Transmission Network Access (Annex 1 to the Frame Capacity Contract, version of 23 September 2013), differs from Eustream's: it takes the fee of the *first* months instead of the two most expensive ones, has no neutrality charge, and covers day contracts with a one-off activation deposit instead.

## What Changes

- The TSO dropdown on tab 3 offers Gas Connect Austria after Eustream; Eustream stays the default.
- With GCA chosen, the network point dropdown lists GCA's single sides as on tab 2, and the stage selector and the CEGHIX box are hidden; the auction surcharge box stays.
- GCA's security deposit (GTC IV para. 15), taken from tab 2's monthly invoice after the surcharge:
  - month: the whole capacity fee;
  - quarter: the fee of the first two months;
  - gas year: the fee of the first three months;
  - day: no security deposit; the guarantee cells show "–" and count as 0 in the total, and a note under the table says that GCA's one-off EUR 100,000 activation deposit covers day contracts.
- GCA's commodity charge is added to its guarantee: the volume at full use of the capacity during the months the guarantee covers, times the entry or exit rate (from 1 January 2026: 0.03322 / 0.11963 EUR/MWh; from 1 January 2027: 0.07914 / 0.2586 EUR/MWh; 0 before 2026). Two new columns, "Commodity fee" and "Commodity fee guarantee", sit next to the GfON columns; Eustream rows show "–" in them.
- A GCA row shows "–" for Stage, CEGHIX, GfON fee and GfON fee guarantee; its total guarantee is its capacity fee guarantee plus its commodity fee guarantee.
- A closed expander "How Gas Connect Austria calculates the financial guarantee" describes the rule: how much, the activation deposit, when, how long, what happens if it is missed, and the forms.
- The EUR 100,000 activation deposit is only described in words; it is never added to a row or to the total.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `bank-guarantee-calculator`: the TSO dropdown gains GCA; the stage and CEGHIX inputs become Eustream-only; the table gains the commodity fee columns and shows dashes for GCA's stage, GfON and day guarantees; GCA's guarantee rule (capacity fee plus commodity charge) and its description are added.

## Impact

- `core/guarantee.py`: a GCA rule and note next to Eustream's, and a way to price a booking without a stage.
- `app.py` (tab 3): hiding the stage and CEGHIX for GCA, the "–" cells, and the day note under the table.
- Tests: `tests/test_guarantee.py` (GCA rule) and `tests/test_app.py` (the TSO dropdown no longer offers only Eustream; GCA inputs and rows).
- No change to tabs 1 and 2, the tariff file or the Excel workbook.
