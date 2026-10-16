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
