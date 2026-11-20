## 1. Core rule (`core/guarantee.py`)

- [x] 1.1 Make `capacity_fee_guarantee` optional in `GuaranteeResult` and let `total_guarantee` return `None` when both guarantees are `None`, else their sum with `None` as 0; verify that the existing Eustream tests in `tests/test_guarantee.py` still pass
- [x] 1.2 Add `STAGED_TSOS = {EUSTREAM}` and let `calculate_guarantee` accept `stage=None` (and ignore the CEGHIX) for a TSO outside it, while still rejecting an unknown stage for Eustream; verify with a new test that Eustream without a stage still raises `ValueError`
- [x] 1.3 Add `gca_guarantee` (month: whole fee; quarter: first two invoice lines; gas year: first three; day: `None`) and register it in `GUARANTEE_RULES` after Eustream; verify with tests in `tests/test_guarantee.py` for the spec's GCA scenarios (quarter 100,064.00; gas year 64,200.00; month in kWh/d 62,676.00; day "–"; quarter +10% 110,070.40; day +2.5% fee 2,681.40), built on the synthetic `make_row` table, plus one check against the real file
- [x] 1.4 Add `GCA_NOTE` (how much, activation deposit, when, how long, if missed, forms; GTC version of 23 September 2013, German binding) to `GUARANTEE_NOTES` and `GCA_DAY_NOTE` with the spec's text; verify with a test that the note mentions the first two and three months, EUR 100,000 and 5 working days

## 2. Tab 3 (`app.py`)

- [x] 2.1 Show the stage radio and the CEGHIX box only for a TSO in `STAGED_TSOS`, and store `stage=None, ceghix=None` for the others; verify in `tests/test_app.py` that choosing GCA hides both and still shows the surcharge box
- [x] 2.2 In `guarantee_record`, show "–" for Stage and CEGHIX when the booking has none and for a `None` capacity fee or total guarantee, and in `guarantee_total` count `None` as 0; verify in `tests/test_app.py` with the spec's mixed list (total guarantee 380,168.80)
- [x] 2.3 Show `GCA_DAY_NOTE` under the total when a priced row is a GCA day; verify in `tests/test_app.py` that it appears with a GCA day row and not without one
- [x] 2.4 Update the app test that asserts the TSO dropdown offers only Eustream to expect `["Eustream", "Gas Connect Austria"]`, with Eustream chosen; verify that `pytest` passes in full

## 3. Wrap-up

- [x] 3.1 Run the app locally (restart Streamlit after the `core/` edits), add one GCA quarter, one GCA day and one Eustream booking, and check the table, the total and the day note by eye
- [x] 3.2 Mention GCA on tab 3 in `README.md` ("So far it knows Eustream's rule", the tab 3 section) and on the promo page (`docs/index.html`, "The guarantee tab knows only Eustream's rule so far."), and log the implementation decisions in `PLANNING_LOG.md`; verify with a grep that neither still says only Eustream

## 4. GCA commodity charge

- [x] 4.1 Add `commodity_fee` and `commodity_fee_guarantee` to `GuaranteeResult`, count the commodity guarantee in `total_guarantee`, and add `GCA_COMMODITY_RATES` and the commodity charge to `gca_guarantee` (same months as the capacity fee guarantee, 0 before 2026, none for a day's guarantee); verify with tests in `tests/test_guarantee.py` for the spec's commodity scenarios (Q4 2026 31,697.16 / 21,016.60; gas year 2025/26 94,057.89 / 0.00; gas year 2026/27 235,018.83 / 31,697.16; December 150,000 kWh/h 13,350.71; Oberkappel entry 20,513.09 / 13,447.47; day 344.53 / "–"; surcharge leaves it unchanged)
- [x] 4.2 Describe the commodity charge and its four rates (0 before 2026) in `GCA_NOTE`; verify with the note test
- [x] 4.3 Add the "Commodity fee" and "Commodity fee guarantee" columns to tab 3's table and total row ("–" for Eustream rows and for a GCA day's guarantee); verify in `tests/test_app.py` with the spec's mixed list (commodity 32,041.69 / 21,016.60, total guarantee 401,185.40), and update the existing column and row assertions
- [x] 4.4 Update the README's Gas Connect Austria paragraph with the commodity charge, run the full `pytest`, restart the running app and check tab 3 by eye; log the implementation in `PLANNING_LOG.md`
