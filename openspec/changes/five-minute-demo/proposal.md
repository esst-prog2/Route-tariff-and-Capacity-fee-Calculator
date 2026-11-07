## Why

README section 1 ("The demo") was written for a three-minute live run with a projector, and it has grown into two long walk-throughs of tabs 1 and 2 with every edge case. It does not mention tab 3 (Bank Guarantee Calculator) at all. The demo is now a five-minute presentation from screenshots, and the audience scores the program right after it, so section 1 has to describe one short path through the program that the screenshots can follow.

## What Changes

- Section 1 is rewritten as three to six sentences, in the present tense, naming the real file, the hosted app's address, the three tabs and one example per tab with its real figures:
  - Tab 1, Route Tariff Calculator: BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU, 2026-10-01 to 2027-03-31, 400 HUF per EUR, route total 3.6957 EUR/MWh, 0.2956 cheaper than without quarterly products.
  - Tab 2, Capacity Fee Calculator: the bundled point Mosonmagyaróvár AT>HU, Quarter 2026 Q4, 50,000 kWh/d: Gas Connect Austria exit 2,605.83 EUR, FGSZ entry 782,558 HUF, bundle total 4,584.48 EUR at 395.5 HUF per EUR.
  - Tab 3, Bank Guarantee Calculator: Eustream Balassagyarmat SK>HU, Quarter 2026 Q4, 100,000 kWh/h, booked capacity, CEGHIX 30: capacity fee 361,344.00 EUR, total guarantee 280,104.80 EUR.
- The current long walk-throughs of tabs 1 and 2 are not deleted. They move, with the same wording and figures, to a new section "## Walk-through of tabs 1 and 2" after "Running the MVP", next to the existing workbook and tab 3 sections, so the detail (over-booking, interruptible points, tariff changes, invoice splits, LNG entries) stays documented.
- No code, test, tariff or spec changes. Every figure in the new section 1 is already checked by an existing test.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None. This change is documentation only, so it sets `skip_specs: true`.

## Impact

- `README.md`: section 1 replaced; a new section with the old walk-throughs.
- `PLANNING_LOG.md`: the decisions of this change.
- Nothing else. The figures quoted are covered by existing tests: `tests/test_route.py` (3.6957, 3.9913, 0.2956), `tests/test_bundle_fee.py` and `tests/test_app.py` (4,584.48), and `tests/test_app.py` tab 3 (361,344.00 and 280,104.80).
