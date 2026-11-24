## Why

Tab 3 prices the guarantee for Eustream, Gas Connect Austria, FGSZ and NET4GAS, but routes from and through Bulgaria start at Bulgartransgaz, whose credit limit rules are in chapter 8 of the General Terms and Conditions to its Harmonized Contract for Access and Natural Gas Transport (approved on 15 September 2026).

## What Changes

- The TSO dropdown on tab 3 offers Bulgartransgaz after NET4GAS, with its 13 single sides as on tab 2. Like GCA, FGSZ and NET4GAS it hides the stage and CEGHIX and keeps the auction surcharge.
- Bulgartransgaz's guarantee is the amount reserved from the credit limit (8.10): 6% of a gas year's value, 25% of a quarter's, 70% of a month's and 100% of a day's, the value including the auction premium, plus 20% VAT, always.
- A "Bundled capacity" checkbox, only for Bulgartransgaz, counts half of the auction premium (8.11); the capacity fee shown keeps the full premium. A "Bundled" column appears when the list has a Bulgartransgaz row.
- Bulgartransgaz's transport price on allocated quantities (Contract 4.5, GTC 7.3) is not reserved (8.10 covers capacity and the premium only), so Bulgartransgaz has no commodity fee. The "Commodity / volume fee" columns are left out of the list and total table when no row has a commodity fee, e.g. a list of only Eustream and Bulgartransgaz rows.
- The minimum credit limit of EUR 2,500 (8.2) is described in words only. The product's value uses tab 2's tariff for the product, not the auction-date tariff 8.10 names; the description says so.
- A closed expander "How Bulgartransgaz calculates the financial guarantee" describes chapter 8: how much, the minimum, release, what happens when it is drawn on, and the forms.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `bank-guarantee-calculator`: the TSO dropdown gains Bulgartransgaz, the inputs gain the bundled checkbox, the table gains the Bundled column; Bulgartransgaz's rule and description are added.

## Impact

- `core/guarantee.py`: `bulgartransgaz_guarantee`, `BULGARTRANSGAZ_SHARE`, `BULGARTRANSGAZ_VAT`, `BULGARTRANSGAZ_NOTE`, `asks_bundled`, and a `bundled` argument to `calculate_guarantee`.
- `app.py` (tab 3): the checkbox, the booking's `bundled` value and the Bundled column.
- Tests: `tests/test_guarantee.py` and `tests/test_app.py`.
- `README.md` and the promo page (`docs/index.html`) name Bulgartransgaz on tab 3.
- No change to tabs 1 and 2, the tariff file or the Excel workbook.
