## Context

Tab 3 already has room for more TSOs: `core/guarantee.py` maps each TSO to a rule (`GUARANTEE_RULES`, `FeeResult` + CEGHIX -> `GuaranteeResult`) and a note (`GUARANTEE_NOTES`), and `app.py` fills the TSO dropdown from `GUARANTEE_RULES`. Tab 2 already prices GCA (`calculate_fee`, with GCA's tariff cells billed at 4 decimals and its gas years and quarters in equal months). Three things don't fit GCA yet: `calculate_guarantee` requires a stage, `GuaranteeResult.total_guarantee` assumes there is always a capacity fee guarantee, and the app's row builder reads the stage and CEGHIX of every row.

## Goals / Non-Goals

**Goals:**
- Add GCA as a second rule without changing any Eustream figure or behaviour (all existing tests keep passing, except the one that asserts that the dropdown offers only Eustream).
- Keep the TSO-specific logic in `core/guarantee.py`, so that the app only asks which inputs a TSO needs.

**Non-Goals:**
- No activation deposit amount anywhere in the calculations.
- No newer GCA GTC version; the 2013 annex is the source.
- No other TSOs (FGSZ, NET4GAS, Gastrans).

## Decisions

**1. Which inputs a TSO needs comes from `core/guarantee.py`.** A set such as `STAGED_TSOS = {EUSTREAM}` (TSOs whose guarantee depends on the stage, and so on the CEGHIX). `app.py` shows the stage radio and the CEGHIX box only for these TSOs. For any other TSO it stores the booking with `stage=None, ceghix=None`. *Alternative:* `if tso == EUSTREAM` in the app, rejected because it spreads TSO knowledge into the UI.

**2. `calculate_guarantee` accepts `stage=None` for unstaged TSOs.** It still validates the stage for staged TSOs. For an unstaged TSO it ignores the stage and the CEGHIX and calls the rule with `ceghix=None`. The surcharge path (`parse_surcharge`, `with_surcharge`) is shared unchanged.

**3. The GCA rule takes the first N invoice lines.** `gca_guarantee(result, _ceghix)` takes N = {MONTH: all, QUARTER: 2, GAS_YEAR: 3} from `result.invoice` in date order (the invoice is already in date order). These are tab 2's invoice cents after the surcharge split, so the guarantee is exactly what the first invoices will say. A DAY gives `capacity_fee_guarantee=None`. *Alternative:* recompute the first months from the exact fee, rejected because the trader pays the invoices, and the invoices are already rounded.

**3a. The commodity charge follows the GfON's pattern.** `GuaranteeResult` gains `commodity_fee` and `commodity_fee_guarantee` (`None` for Eustream), and `total_guarantee` adds the commodity fee guarantee. The rates are a small dated table in `core/guarantee.py` (`GCA_COMMODITY_RATES`: valid from, entry rate, exit rate), not in the tariff file, because the file has no commodity column and the rates come from the user, not from the export. The volume of an invoice line is kWh/d × days / 1000 MWh, priced at the rate valid on the line's first day. That is exact because every rate change falls on 1 January. Before the first date the rate is 0 (the user's choice). The commodity guarantee uses the same invoice lines as the capacity fee guarantee, so the two always cover the same months. *Alternative:* a commodity column in the tariff file, rejected because it changes the file format and the loader for two numbers a year.

**4. `GuaranteeResult.capacity_fee_guarantee` becomes `int | None`.** `total_guarantee` returns `None` when both guarantees are `None`, and otherwise the sum counting `None` as 0. The app already turns `None` into "–"; `guarantee_total` counts `None` as 0 (as it does for the GfON). *Alternative:* store 0 and render 0.00, rejected because the user chose "–", which says "not required" rather than "zero".

**5. Display rules stay in `guarantee_record`.** Stage shows "–" when the booking's stage is `None`, and the CEGHIX column shows "–" when there is no CEGHIX. The day note is a `st.caption` under the total. It is shown when any priced row is a GCA day, i.e. its point's TSO is GCA and its instrument is DAY; the note text is kept in `core/guarantee.py` (`GCA_DAY_NOTE`).

**6. Session state.** The stage radio keeps its key `guar_stage`. When GCA is chosen the radio is simply not rendered, so switching back to Eustream finds the earlier value. Streamlit drops the state of widgets that are not rendered, so it may reset to the default "Booked capacity". Either is acceptable.

## Risks / Trade-offs

- [The 2013 GTC may be out of date; GCA's current rules may differ] → The expander names the version and its date, and says the German text is binding; switching to a newer version later only changes `gca_guarantee` and `GCA_NOTE`.
- [The first-months rule gives a lower guarantee than Eustream's for a gas year that starts on the cheaper tariff, e.g. 64,200 vs 79,400 EUR] → This is what the GTC says; the gas year scenario pins it down, so no one "fixes" it to the two largest months.
- [Removing an Eustream-only assumption (`stage` always set) could break existing rows] → Existing bookings in a session always have a stage; the new `None` path is only taken for TSOs outside `STAGED_TSOS`.
- [The commodity rates are typed into the code and will go out of date when GCA publishes new ones] → They sit in one dated table next to the GCA rule; a new year is one more line. Before 2026 they count as 0, which the GCA description states.
- [A cent difference between invoices after a surcharge split] → Inherited from tab 2's `split_by_weights`; the guarantee follows the invoices, as for Eustream.
