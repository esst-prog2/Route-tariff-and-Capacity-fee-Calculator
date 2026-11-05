## Context

The motivation is in proposal.md. The requirements are in `specs/bank-guarantee-calculator/spec.md`.

- Tab 2 already prices a single-side booking with `fee.calculate_fee`. It returns the total and a monthly invoice in minor units (cents). For Eustream, a gas year and a quarter are already split into twelfths and thirds at the tariff valid in each month.
- All of Eustream's points in the tariff file are in EUR and priced per kWh/h, so tab 3 needs no FX rate.
- The app is a single `app.py` Streamlit script with the rules in `core/`. Each rule is tested with hand-worked figures.

## Goals / Non-Goals

**Goals:**
- Keep the guarantee rules in `core/`, as pure functions that use exact `Fraction` amounts and are testable without Streamlit.
- Add another TSO later by writing one rule function. The tab itself should not need to change.
- Reuse tab 2's capacity fee. Do not compute it a second time.

**Non-Goals:**
- Saving the list beyond the browser session, or exporting it.
- Bundled points and LNG entries. A guarantee is asked for per TSO, so the tab works on single sides.

## Decisions

### A `core/guarantee.py` module with one rule per TSO

- `GUARANTEE_RULES = {EUSTREAM: eustream_guarantee}` maps a TSO code to a function. The function takes the `FeeResult` and the optional CEGHIX and returns a `GuaranteeResult`:
  - capacity fee, GfON fee, capacity fee guarantee, GfON fee guarantee, total guarantee;
  - each in cents, with `None` for an auction row's GfON fields.
- The TSO dropdown lists the keys of this map.
- *Alternative:* a single function with TSO `if`s. It is rejected because each TSO's rule (7.6.2 for Eustream) reads and changes on its own, and the map makes "which TSOs are supported" a single fact.

### The capacity fee guarantee comes from tab 2's invoice lines

- The "two most expensive months" are the two largest `InvoiceLine.amount` values. These are the amounts Eustream actually invoices, and they already add up to the shown total.
- *Alternative:* recompute the monthly exact amounts. It is rejected because it could differ from the invoice by a cent.

### GfON is computed per calendar month of the product

- The volume of each month is capacity (kWh/h) × 24 × the days of the product in that month / 1000. The capacity comes from `FeeResult.capacity_kwh_d / 1000` MWh per day.
- The GfON fee is the rounded exact total.
- The guarantee is the rounded exact sum of the two largest months. For a month or a day, it is the fee.
- Rounding uses `money.round_minor` (half up), as tab 2 does.
- The month split comes from the invoice lines' `days`. That way the GfON months always match the capacity fee months.

### The "longer than two months" test goes by instrument

- A gas year and a quarter use the two-month rule. A month and a day use the total.
- The tab only offers these four instruments, so this is exact. No product has exactly two months.

### Rows store inputs; figures are recomputed on each run

- `st.session_state["guarantee_rows"]` holds a list of small dicts: point key, instrument, period selection, capacity text, unit, stage, CEGHIX text.
- On each rerun, the table is rebuilt from the current tariff table. A new tariff file therefore updates the figures.
- Validation runs on "Add to list", so a stored row is always valid against the table it was added with.
- If a later tariff file no longer prices a stored row, the tab shows that row's no-tariff message and leaves the row out of the total. It does not crash.

### Row removal uses `st.dataframe` row selection

- The table is an `st.dataframe` with `on_select="rerun"` and `selection_mode="multi-row"`. "Remove selected rows" drops the selected indices. "Clear list" empties the list.
- The total row is shown under the table as a separate one-row frame, so it can never be selected and removed.
- *Alternative:* a remove button per row (`st.columns` loops). It is rejected because the layout is clumsy for 11 columns.

### Tab 2's period pickers become a shared helper

- The instrument and period widgets move into `choose_product(table, booked, today, key_prefix)` in `app.py`. Tab 2 uses the `fee_` prefix and tab 3 uses `guar_`.
- Tab 2's widget keys stay `fee_*`, so its existing app tests still pass.

## Risks / Trade-offs

- [CEGHIX is typed per row and could be mistyped] → The value is shown in its own column next to the result, so a typo is visible.
- [Eustream may count the 25-hour and 23-hour gas days in GfON] → The spec states 24 hours per day as the user's choice. A later change can switch to real gas-day hours in one function.
- [Eustream's domestic point is not in the catalog] → It is noted in the proposal as not covered. It can be added when the catalog learns the "EUS->SK" names.
- [Session-only list is lost on page reload] → This is accepted for now. An export can come later.
