## Why

The Stage, CEGHIX and GfON columns on tab 3 only ever hold a value for Eustream rows. A list of Gas Connect Austria and FGSZ bookings shows four columns of "–", which makes an already wide table harder to read.

## What Changes

- The Stage, CEGHIX (EUR/MWh), GfON fee and GfON fee guarantee columns are shown only when the list holds at least one Eustream row, in the list and in the total table.
- With no Eustream row they are left out; the other columns keep their order. Adding an Eustream booking brings them back, with "–" in the other rows as before.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `bank-guarantee-calculator`: the "Table columns and total" requirement shows the Stage, CEGHIX and GfON columns only when the list has an Eustream row.

## Impact

- `app.py` (tab 3): leaves the four columns out of both tables when no row is Eustream.
- `tests/test_app.py`: one GCA-only assertion shifts (its column slice), and a new test covers lists with and without Eustream.
- No change to the calculations, the inputs, or tabs 1 and 2.
