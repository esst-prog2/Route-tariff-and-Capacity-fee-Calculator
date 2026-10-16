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
