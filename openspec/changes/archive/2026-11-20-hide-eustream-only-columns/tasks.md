## 1. Tab 3 (`app.py`)

- [x] 1.1 Add `EUSTREAM_ONLY_COLUMNS` and drop them from the list and total DataFrames when no booking's TSO is in `guarantee.STAGED_TSOS`; verify with a new test in `tests/test_app.py` that a GCA + FGSZ list has neither the columns nor the total columns, and that adding an Eustream booking brings them back with "–" in the other rows
- [x] 1.2 Update the GCA-only assertion in `test_tab3_gca_gas_year_and_surcharge` to the narrower table, and verify that the full `pytest` passes

## 2. Wrap-up

- [x] 2.1 Restart the running app and check a GCA-only list by eye; mention in the README's tab 3 list paragraph that the CEGHIX and GfON columns appear only with an Eustream row; log the implementation in `PLANNING_LOG.md`

## 3. Stage column

- [x] 3.1 Add "Stage" to `EUSTREAM_ONLY_COLUMNS`, update the column assertions of the GCA-only and new tests, run the full `pytest`, restart the app and check a GCA + FGSZ list by eye; update the README sentence and `PLANNING_LOG.md`
