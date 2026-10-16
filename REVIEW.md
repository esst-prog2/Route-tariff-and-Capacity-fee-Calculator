# Whole-codebase review

Most of this code was written by the agent, change by change. Each section below is one pass over the
whole repository looking for one kind of problem, followed by what was done about it. Every pass is its
own commit on the `hw6-review` branch.

## 1. Code against the spec

Read the four specs in `openspec/specs/` next to `core/` and `app.py`, looking for behaviour the specs
describe but the code does differently, and for code the specs never asked for.

Found:
- **Bundle "no tariff" message gave the wrong day.** For a bundle, `calculate_bundle_fee` rebuilt the
  message with the product's first day. Since products are priced part by part, the side can have a
  tariff on that day and lose it later in the period, so the message named a day that *does* have a
  tariff. The spec (and the decision logged on 2026-10-13) says the message names the first day
  without a row.
- **Stale docstring.** `PriceOracle` in `core/optimizer.py` still said prices are "in HUF per 1 kWh/h",
  from the FGSZ-only first version; the oracle now works in each TSO's own currency and unit.
- Kept on purpose: the environment variable is still called `FGSZ_TARIFF_FILE` although the app now
  covers 21 TSOs. The README documents it, and renaming it would silently break anyone who set it.

Done:
- `NoTariffError` now carries the day, and the bundle message uses it. New test
  `test_bundle_side_whose_tariff_ends_inside_the_period_names_the_first_day_without_one` (red before
  the fix, green after).
- Docstring corrected.

## 2. Rules patched where they broke instead of where they are wrong

Read the commit history (52 commits) and the rule-heavy code for fix-on-fix chains: a rule that was
wrong once and then got an exception added for every case that hit it.

Found:
- The history itself has no "fix ... fix again" chains: every change of a rule (over-booking, the gas
  year product, part-by-part pricing, the map instead of the corridor) went through an OpenSpec change
  that replaced the rule in one place (`TariffTable.product_price` serves both tabs).
- **Point names had two override layers on top of the cleaning rule.** `build_catalog` took a point's
  name from the hand-written `POINTS` list (30 points from the FGSZ-only first version), else from
  `FLOW_OVERRIDES`, else from `EIC_NAMES`, else from the cleaning rule; and a name in `POINTS` also
  won over the other TSO's side of the same EIC. When the catalog was added, the old list was kept
  as a patch instead of folded into the rule. Checked: on both tariff files the rule already gives
  24 of the 30 names and every flow; the other 6 belong to 4 EICs (Beregdaróc, Balassagyarmat,
  Strandzha 1/Malkoclar, Negru Voda 1/Kardam), and `EIC_NAMES` is exactly the place for those.
- The list was also quietly naming points in the tests' hand-made tables, whose rows were all called
  "Test point" (no flow), so those tests only worked through the patch.

Done:
- The 4 names moved into `EIC_NAMES`; `POINTS` and its two lookups are gone from `build_catalog`. The
  rule is now: name = `EIC_NAMES`, else the most common cleaned name of the EIC; flow =
  `FLOW_OVERRIDES`, else the cleaning rule.
- Checked by comparing the full catalog and network (109 single sides, 14 LNG entries, 43 bundles,
  22 map points) before and after on the real and the sample file: identical.
- The 30-point list moved to `tests/helpers.py` as `KNOWN_POINTS`, so it is now an expectation that
  the rule must keep meeting (`test_known_points_keep_their_names_in_the_catalog`), not a patch. The
  test tables now name their rows like the real file does (`name (flow)`).

## 3. The same job done twice

Looked for functions, constants and blocks that do almost the same thing under different names,
the kind of thing that appears when each change is written without seeing the rest.

Found and merged (one copy kept each):
- `dates_text` was defined in `app.py` and in `core/fee.py`, character for character. The app now
  uses the one in `core/fee.py`.
- **Exchange-rate parsing was written twice.** `core/route.py` had `parse_fx_rate` for tab 1, and
  `bundle_eur_total` in `core/fee.py` parsed the tab 2 rate boxes with its own copy of the same
  rules. Both now use `parse_fx_rate`, moved with `rate_message` to `core/money.py`.
- `EUR = "EUR"` was defined in both `fee.py` and `route.py` (and `route.py` also compared with the
  bare string). It now lives once in `core/money.py`.
- **The kWh/h to kWh/d conversion was written twice.** `route.py` had `HOURS_PER_UNIT`, and `fee.py`
  had `HOURS_PER_DAY = 24` with its own `if unit == "kWh/h" ... else` (which also treated any other
  unit as kWh/d without saying so). `HOURS_PER_UNIT` now sits next to the TSO table in
  `core/tariffs.py`, and both use it.
- The "at 1 EUR = 400 HUF" caption text was built twice in `app.py`; now `rates_text`.

Found and left:
- Choosing the price cell for a product is done in `fee._price_cell` (tab 2's instruments: gas
  year, quarter, month, day) and `route._segment_cell` (the optimiser's products: yearly,
  quarterly, monthly). They are short and each follows its own tab's vocabulary, which the specs
  and the UI labels use; merging them would mean a third set of names.

## 4. Errors that disappear

Searched every `except`, and every place where a failed step just leaves something out, for errors
that are caught and then never reach the user.

Found and fixed:
- **`resolve_period` swallowed `TypeError` and `ValueError` with `pass`** and turned them into
  "Choose a product period.". The intent was "a picker is still empty", but the same `except` also
  hid real bugs (an impossible month, a wrong argument) behind that harmless-looking prompt. It now
  checks for the missing selection explicitly; anything else raises. Test:
  `test_an_impossible_period_raises_instead_of_reading_as_an_incomplete_selection`.
- **A point whose name has no border flow vanished.** `build_catalog` skipped any side for which no
  flow (like `RO>HU`) could be read from its `Network point` text, with no message. On the committed
  files no side is lost this way, but in an uploaded file a point would simply be missing from both
  tabs. The catalog now lists those sides (`Catalog.unnamed`) and the sidebar shows them, like the
  excluded rows. Tests: `test_a_side_whose_name_has_no_flow_is_reported_not_dropped_silently`,
  `test_a_point_without_a_flow_in_its_name_is_listed_in_the_sidebar`.

Checked and kept:
- `load_tariffs` catches every exception while opening the Excel file, but turns it into an error
  shown on the page (with the exception text) and stops; nothing carries on with empty data.
- `optimizer._optional_price` catches `PriceUnavailable` and drops that product as an option. The
  spec asks for exactly that for a product starting before the period with no tariff on some day;
  a day that is really requested and has no tariff still raises and is shown as a message.
- `parse_fx_rate` and the capacity parsing catch `ValueError` and return the message the user sees.

## 5. Quiet defaults

Looked at every default value and every `.get(key, default)` for the ones where a missing value is
really a mistake but the code quietly picks something instead.

Found and fixed:
- **`TariffRow` defaulted to HUF, kWh/h and Firm.** Left over from the FGSZ-only version: a row built
  without its currency would silently have become a forint row priced per kWh/h. The loader always
  passes all three, so the defaults only hid mistakes; they are now required.
- **`parse_fx_rate(text, currency="HUF")`**: a caller forgetting the currency would get messages
  about the HUF rate. The currency is now required.
- **The bundle EUR total divided by `rates.get(currency, 1)`**, so a currency without a rate would
  have counted 1:1 as euros. Today the missing rates are caught just before, but the fallback was a
  trap; it now uses 1 only for EUR itself and fails loudly otherwise.
- `tso_name` returned the raw operator code for an unknown TSO; only the 21 known TSOs can reach it,
  so an unknown one is now an error instead of a strange label.
- **A file without a `Capacity_fee` sheet was read from its first sheet without saying so.** Kept,
  because a renamed sheet should still work, but the sidebar now says which sheet was read.
  Test: `test_a_file_without_the_capacity_fee_sheet_says_which_sheet_it_read`.
- **A map point without a typed-in position got no marker, silently.** With an uploaded file, a new
  border point would be routable from the "Next point" list but missing from the map. Such points are
  now named under the map. Test: `test_a_border_point_without_a_map_position_is_named_under_the_map`.

Checked and kept: the route defaults to an empty route when the file lacks the default points (the
tab then asks for the first point), and `resolve_tariff_path` falls back to the committed real file
when the variable is unset, as the spec says.

## 6. Dependencies

Checked every third-party import against `requirements.txt`, whether each package really exists
under that name, whether it is used, and whether its version is pinned.

Found:
- All four listed packages (`streamlit`, `pandas`, `openpyxl`, `pytest`) exist on PyPI under exactly
  these names and are the well-known projects, not look-alikes; each is used (`openpyxl` only
  indirectly, as the engine pandas reads `.xlsx` files with).
- **Nothing was pinned** (`streamlit>=1.50` and so on), so the hosted app installs whatever is newest
  at each redeploy, not what the tests ran with. PyPI already has Streamlit 1.66 and pandas 3.0.6,
  while the suite was run with 1.64.0 and 3.0.2.
- **`altair` is imported directly** by `app.py` (the route map) but was not listed; it only arrived as
  a dependency of Streamlit.
- No package is imported without being needed, and the standard library covers the rest.

Done: `requirements.txt` pins the exact versions the 352 tests pass with and lists `altair`, with a
note on what each is for.

## 7. Dead code

Counted, for every public function, method, field and constant, where it is used: in `app.py`, in
`core/`, or only in the tests. Code that only tests read is still code nobody runs.

Found and removed:
- **`Segment.tariff_used`, `PriceOracle.tariff_used` and `TsoOracle.tariff_used`.** The optimiser
  wrote a "tariff used" text into every product it chose, by looking up the row of every day, but
  nothing shows it: tab 1's Details table builds its own text per point with `point_tariff_used`.
  So every route calculation did that lookup for nothing.
- **The all-daily baseline and its saving** (`Plan.all_daily_total`, `Plan.saving`,
  `TsoLeg.all_daily_per_mwh` / `all_daily_eur_per_mwh`, `RouteResult.all_daily_eur_per_mwh` /
  `saving_eur_per_mwh`). They are left over from before the "next shorter products" comparison; the
  spec now says the tab shows no all-daily figure and no saving against all-daily products.
- `periods.quarter_label`: never called.
- **`spikes/spike_overbooking.py`.** A throwaway script from homework 4 that imports `entries`,
  `exits` and `RouteOracle`, none of which exist any more, so it cannot even start. Its result is in
  the planning log and the script itself stays in the git history (commit `cdece32`).
- Unused imports of `core.points` in three test files.

The tests that read the removed fields now check the same facts through what the app really uses
(`point_tariff_used`, `TsoOracle.sources`, the plan's total).
