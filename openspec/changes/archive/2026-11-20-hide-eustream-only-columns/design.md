## Context

`app.py` builds every tab 3 row with all columns (`guarantee_record`) and the total rows from `GUARANTEE_AMOUNTS` (`guarantee_totals`), then shows them with `st.dataframe`. The Stage, CEGHIX and GfON values come only from Eustream, the one TSO in `guarantee.STAGED_TSOS`.

## Goals / Non-Goals

**Goals:** Leave the four Eustream-only columns out when no row needs them, without touching the calculations.

**Non-Goals:** No per-row column hiding, which a table cannot do.

## Decisions

**Drop the columns from the two DataFrames, not from the records.** `EUSTREAM_ONLY_COLUMNS = ("Stage", "CEGHIX (EUR/MWh)", "GfON fee", "GfON fee guarantee")`. When no booking's TSO is in `guarantee.STAGED_TSOS`, the tab calls `DataFrame.drop(columns=...)` on both the list and the total table. The rows and totals keep being built the same way, so `guarantee_record` and `guarantee_totals` stay simple and their outputs stay complete. Keying on `STAGED_TSOS` ties the rule to the TSOs that have a stage, CEGHIX and GfON, rather than to a hard-coded name. *Alternative:* skip the keys while building each record. Rejected, because it would need the list-wide decision passed into every row builder.

## Risks / Trade-offs

- [Columns appear and disappear as Eustream rows are added or removed, so the table's shape changes] → Expected and asked for. The other columns keep their order, so the eye still finds them.
