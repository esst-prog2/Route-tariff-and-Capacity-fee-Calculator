## 1. Guarantee rules in core

- [ ] 1.1 Create `core/guarantee.py` with `GuaranteeResult` (capacity fee, GfON fee, capacity fee guarantee, GfON fee guarantee and total guarantee in cents, GfON fields `None` at auction), `gfon_rate(ceghix)` = (CEGHIX + 1) × 0.85 / 100 and `parse_ceghix` with the message "CEGHIX must be a positive number."; verify with unit tests in `tests/test_guarantee.py` (rate 0.2635 for CEGHIX 30, 0.3485 for 40; blank, 0, -5 and "abc" rejected)
- [ ] 1.2 Implement `eustream_guarantee(fee_result, ceghix)`: capacity fee guarantee = two largest invoice lines for a gas year or quarter, else the total; GfON volume per month from the invoice lines' days at 24 h/day, fee and two-largest-month guarantee rounded half up to cents; register it in `GUARANTEE_RULES`; verify with tests on hand-made tariff rows (`tests/helpers.py`) covering all four instruments, a tariff change inside a gas year, a kWh/d capacity and an auction row
- [ ] 1.3 Add the spec's Balassagyarmat SK>HU worked figures as tests on the real tariff file (Q4 2026 booked 280,104.80 / auction 240,896.00, gas year 2025/26 21,245.68, January 2027 140,060.40, 5 Dec 2026 auction 7,896.00, list total 428,061.20); verify `python -m pytest tests/test_guarantee.py` passes

## 2. Shared product pickers

- [ ] 2.1 Move tab 2's instrument and period widgets into a `choose_product(table, booked, today, key_prefix)` helper in `app.py`, keeping tab 2's `fee_*` keys; verify the existing tab 2 app tests pass unchanged

## 3. Tab 3 in the app

- [ ] 3.1 Add the "Bank Guarantee Calculator" tab with the TSO dropdown (keys of `GUARANTEE_RULES`), network point, product pickers (`guar_` keys), capacity and unit, stage (default "Booked capacity") and, for booked capacity only, the CEGHIX box with its note; verify with an app test that the box shows for "Booked capacity" and hides for "Capacity auction"
- [ ] 3.2 Add "Add to list" with validation (capacity, no tariff, CEGHIX messages) and session-state rows; verify with app tests that a valid booking adds a row and each invalid case shows its message without adding one
- [ ] 3.3 Render the table with the eleven columns in spec order, "–" for auction GfON cells, EUR amounts with two decimals and thousands separators, and the total row underneath; verify with an app test that the mixed list of the spec shows a total guarantee of 428,061.20
- [ ] 3.4 Add "Remove selected rows" (dataframe multi-row selection) and "Clear list", plus the empty-list message "Add a booking to start the list."; verify with app tests for removing the middle of three rows and for clearing

## 4. Wrap-up

- [ ] 4.1 Add a README section on tab 3 (inputs, the Eustream rule with the Q4 2026 example, CEGHIX of the day before the booking, what is not covered); verify the README figures match the tests
- [ ] 4.2 Run the full test suite (`python -m pytest`) and `openspec validate eustream-bank-guarantee --strict`; verify both pass
- [ ] 4.3 User clicks through tab 3 in the running app (`streamlit run app.py`) with the spec's bookings and confirms the figures
