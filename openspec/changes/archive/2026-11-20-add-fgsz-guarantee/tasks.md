## 1. Core rule (`core/guarantee.py`)

- [x] 1.1 Add `vat` to `GuaranteeResult`, count it in `total_guarantee`, and stop `calculate_guarantee` from refusing non-EUR fees; verify that all existing tests in `tests/test_guarantee.py` still pass
- [x] 1.2 Add `FGSZ_VOLUME_FEE`, `FGSZ_K`, `FGSZ_VAT` and `fgsz_guarantee` (capacity part, volume fee at exit points only, volume part, VAT, each rounded to whole forints once) and register FGSZ in `GUARANTEE_RULES` after GCA; verify with synthetic-table tests (shares, entry F = 0, surcharge leaves F alone, rounding) and a real-file test of every FGSZ scenario in the spec (Csanádpalota quarter 22,729,581; gas year 2026/27 18,375,667; gas year 2025/26 18,384,027; month in kWh/d 26,435,105; day 1,402,151; Mosonmagyaróvár entry 15,901,573; quarter +10% 24,565,266)
- [x] 1.3 Add `FGSZ_NOTE` to `GUARANTEE_NOTES` covering 7.5, 7.2, 7.4.1 (risk classes, multipliers, high-risk extra), deadlines and validity, forms and 7.3; verify with a test that it mentions the phrases of the spec's description scenario

## 2. Tab 3 (`app.py`)

- [x] 2.1 Add the "Currency" column, rename the commodity columns to "Commodity / volume fee" and "Commodity / volume fee guarantee", add the "VAT" column, and format each row's amounts in its own currency; update the column list and every row assertion in the existing tab 3 tests in `tests/test_app.py` (Eustream and GCA amounts unchanged, new cells "EUR" and "–")
- [x] 2.2 Replace the single total row with one "Total" row per currency (EUR, then HUF); verify that the existing EUR-only totals still match and that a list with an FGSZ row shows both rows
- [x] 2.3 Show the "HUF per 1 EUR" box when the list has a HUF row and add the "All in EUR (1 EUR = <rate> HUF)" row for a valid rate, or `money.rate_message("HUF")` for an invalid one; verify in `tests/test_app.py` with the spec's scenario (336,928.75 at 400; the message for "abc"; no box for an EUR-only list)
- [x] 2.4 Update the TSO dropdown test to expect Eustream, Gas Connect Austria and FGSZ, and add an app test that FGSZ shows its 14 points and the surcharge box but no stage, CEGHIX or VAT input, and that an FGSZ row reads as in the spec's quarter scenario; verify that the full `pytest` passes

## 3. Wrap-up

- [x] 3.1 Restart the running app (Streamlit keeps old `core/` modules), add an Eustream quarter, a GCA quarter and an FGSZ quarter, type 400 in the HUF per EUR box, and check the table, the per-currency totals and the combined row by eye
- [x] 3.2 Name FGSZ on tab 3 in `README.md` (the tab 3 section, with the formula, the currency totals and the rate box) and on the promo page (`docs/index.html`, "knows the rules of Eustream and Gas Connect Austria so far"), log the implementation in `PLANNING_LOG.md`, and verify with a grep that neither file still lists only two TSOs
