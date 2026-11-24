## Why

Tab 3 prices the guarantee for Eustream, Gas Connect Austria and FGSZ, but routes towards Germany and Poland run through NET4GAS (Czechia), whose financial security follows Annex No. 1, "Conditions of Financial Eligibility of the Network User", of its Network Code of 7 December 2017. NET4GAS bills in CZK, which tab 3 cannot yet total or convert to EUR.

## What Changes

- The TSO dropdown on tab 3 offers NET4GAS after FGSZ, with NET4GAS's 6 single sides as on tab 2. Like GCA and FGSZ, NET4GAS hides the stage and CEGHIX inputs and keeps the auction surcharge.
- NET4GAS's guarantee is the **transmission risk** of Annex 1 section 9.i, the value of one monthly payment: for a gas year or quarter the most expensive month of the invoice, for a month or day the whole fee, including any auction surcharge. No GfON or VAT.
- At NET4GAS exit points, a **variable part** from NET4GAS's price calculator: OTE index (EUR/MWh) × 0.0009 × CZK per EUR × the product's volume at full use of the capacity. The OTE index and the CZK per EUR rate are typed per booking, in two required boxes shown only for exit points. The variable part is shown in the "Commodity / volume fee" column but not secured, as in NET4GAS's calculator; entry points have none. Two columns, "OTE index (EUR/MWh)" and "CZK per EUR", appear when the list has a NET4GAS exit row.
- The credit limit (8), the daily auction risk (9.ii) and the balancing-transmission risk (9.iii) are described in words only. Czech VAT (21%) is not added, because cross-border transmission for a Hungarian network user is reverse-charged; the description says so.
- **CZK in the table:** NET4GAS rows are in CZK with two decimals and get their own "Total" row after EUR and HUF. A "CZK per 1 EUR" box appears when the list has a CZK row. The "All in EUR" row is shown once every non-EUR currency in the list has a valid rate, and its label names each rate, e.g. "All in EUR (1 EUR = 400 HUF = 25 CZK)".
- A closed expander "How NET4GAS calculates the financial guarantee" describes Annex 1: credit exposure and credit limit, the three risks, VAT, the deadlines, how long the security is kept, and the forms.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `bank-guarantee-calculator`: the TSO dropdown gains NET4GAS; the table gains CZK rows, a CZK total and a CZK rate box, and the combined EUR row covers every currency; NET4GAS's rule and its description are added.

## Impact

- `core/guarantee.py`: `net4gas_guarantee` and `NET4GAS_NOTE`, registered after FGSZ.
- `core/money.py`: a `CZK` constant and `minor_to_major`.
- `app.py` (tab 3): CZK in the currency order, one rate box per non-EUR currency, the combined EUR row over all currencies.
- Tests: `tests/test_guarantee.py` (NET4GAS rule) and `tests/test_app.py` (the TSO dropdown, NET4GAS inputs, a CZK row and the combined row).
- `README.md` and the promo page (`docs/index.html`) name NET4GAS on tab 3.
- No change to tabs 1 and 2, the tariff file or the Excel workbook.
