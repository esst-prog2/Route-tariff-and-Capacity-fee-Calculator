## 1. Core rule (`core/guarantee.py`, `core/money.py`)

- [x] 1.1 Add `net4gas_guarantee` (the largest invoice line) and register NET4GAS in `GUARANTEE_RULES` after FGSZ; verify with synthetic-table tests (a gas year across a tariff change takes the dearer month, a quarter takes a third, a month and a day the whole fee, the surcharge raises it) and a real-file test of every NET4GAS scenario in the spec (Lanžhot CZ>SK quarter 798,512.00; gas year 2026/27 760,000.00; gas year 2025/26 1,300,000.00; month in kWh/d 968,208.00; day 35,496.00; SK>CZ quarter 382,160.00; quarter +10% 878,363.20)
- [x] 1.2 Add `NET4GAS_NOTE` to `GUARANTEE_NOTES` covering credit exposure and limit (8, 9), the three risks, VAT, the deadlines (3), how long (4, 5, 11) and the forms (10); verify with a test that it mentions the phrases of the spec's description scenario
- [x] 1.3 Add `money.CZK` and `money.minor_to_major`

## 2. Tab 3 (`app.py`)

- [x] 2.1 Add CZK to `GUARANTEE_CURRENCIES`, show a "<currency> per 1 EUR" box for each non-EUR currency in the list, and let `guarantee_totals` take a dict of rates and add the "All in EUR" row only when every non-EUR currency has one; verify that the existing HUF tests still pass unchanged
- [x] 2.2 Update the TSO dropdown test to expect NET4GAS last; add app tests that NET4GAS shows its 6 points and the surcharge box but no stage or CEGHIX, and that a list with Eustream, FGSZ and NET4GAS rows shows the CZK row and total, no combined row with only the HUF rate, "All in EUR (1 EUR = 400 HUF = 25 CZK)" with 368,869.23 once both are typed, and the CZK message for "abc"; verify that the full `pytest` passes

## 4. Variable part at exit points

- [x] 4.1 Add `NET4GAS_VARIABLE_FACTOR`, `parse_ote`, `parse_czk_rate`, `asks_variable_inputs` and `net4gas_variable_fee`, and let `calculate_guarantee` take `ote_text` and `czk_rate_text` for a NET4GAS exit point; verify with tests (16.20 CZK on a hand-made month, the surcharge leaves it alone, the messages, an entry point needs no inputs and has 0) and on the real file (the calculator's 413,704.04 and the quarter's 521,380.43)
- [x] 4.2 On tab 3, show the two boxes side by side for a NET4GAS exit point, keep their values with the row, and add the "OTE index (EUR/MWh)" and "CZK per EUR" columns when the list has a NET4GAS exit row; update `add_booking` and the NET4GAS app tests, and verify that the full `pytest` passes
- [x] 4.3 Describe the variable part in `NET4GAS_NOTE` and `README.md`, log it in `PLANNING_LOG.md`, and restart the running app

## 3. Wrap-up

- [x] 3.1 No app was running to restart; start the app to check it boots, then add an Eustream and an FGSZ quarter and a NET4GAS gas year 2025/26 in a scripted run, type 400 and 25 in the rate boxes, and check the table, the per-currency totals and the combined row (388,928.75 EUR)
- [x] 3.2 Name NET4GAS on tab 3 in `README.md` and on the promo page (`docs/index.html`), and log the implementation in `PLANNING_LOG.md`
