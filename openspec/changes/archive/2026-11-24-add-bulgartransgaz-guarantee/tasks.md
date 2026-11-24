## 1. Core rule (`core/guarantee.py`)

- [x] 1.1 Add `BULGARTRANSGAZ_SHARE`, `BULGARTRANSGAZ_VAT` and `bulgartransgaz_guarantee`, register Bulgartransgaz after NET4GAS, and add `asks_bundled` and the `bundled` argument to `calculate_guarantee`; verify with hand-made rows (each product's share and VAT, the full and half premium, rounding, bundled ignored for other TSOs) and the real file (every Bulgartransgaz scenario in the spec)
- [x] 1.2 Add `BULGARTRANSGAZ_NOTE` to `GUARANTEE_NOTES` covering chapter 8; verify with a test of its phrases

## 2. Tab 3 (`app.py`)

- [x] 2.1 Show the "Bundled capacity" checkbox with its note for a Bulgartransgaz point, keep its value with the booking, and add the Bundled column, dropped when no row is Bulgartransgaz
- [x] 2.2 Update the TSO dropdown test and `add_booking`; add app tests for the Bulgartransgaz inputs and description, its rows, the Bundled column and the EUR total; verify that the full `pytest` passes
- [x] 2.3 Drop the Commodity / volume fee columns from both tables when no row has a commodity fee; update the Eustream-only and Bulgartransgaz app tests and check that an FGSZ row brings the columns back

## 3. Wrap-up

- [x] 3.1 Name Bulgartransgaz on tab 3 in `README.md` and on the promo page, and log the implementation in `PLANNING_LOG.md`
- [x] 3.2 Start the app for the user to check (it started and answered on port 8501); the bundled and plain Bulgartransgaz quarters and their total (113,319.76 EUR) are checked in the scripted app tests
