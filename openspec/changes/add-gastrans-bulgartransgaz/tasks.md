## 1. Tariff loading

- [x] 1.1 Add the per-TSO format map (FGSZ HUF/kWh/h, Gastran EUR/kWh/h, BGTRGAZ EUR/kWh/d) and widen the scope filter to the three operators; verify a tariffs test that loads hand-made rows of all three TSOs
- [x] 1.2 Skip BGTRGAZ rows in BGN silently and keep reporting any other currency or unit mismatch; verify tests that BGN rows produce no warning and that an FGSZ row in EUR and a Gastrans row in kWh/d are excluded and reported
- [x] 1.3 Apply the Firm-else-Interruptible rule per (operator, EIC, direction), never mixing types for one point, and store currency, unit and capacity type on each row; verify tests for "Interruptible rows ignored" and "Interruptible used where Firm is missing"
- [x] 1.4 Key `TariffTable` by (operator, EIC, direction) and add a capacity-type lookup per point; verify the "Same EIC and direction at two TSOs" test (Gastrans vs Bulgartransgaz entry at 58Z-000000007-KZ)
- [x] 1.5 Update the test helpers (`make_row`) for operator, currency and unit, and verify the existing tariff tests still pass

## 2. Points and corridor

- [x] 2.1 Add `tso` to `Point`, the TSO display names, and the 30-point table from the spec; verify a points test for 13 / 4 / 13 points per TSO and unique tab 2 labels per TSO
- [x] 2.2 Add the corridor (countries, country TSO, border EICs) and `route_points(begin, end)`; verify a test of all six country pairs against the "Route points" scenarios, including HU->RS using `…505P`, not `…154S`
- [x] 2.3 Check every point in the table has rows in the synthetic sample with the expected capacity type; verify a sample-based test

## 3. Route calculator

- [x] 3.1 Replace `RouteOracle` with a per-TSO oracle summing any number of one TSO's points; verify the "Summing entry and exit" test (Gastrans December 2026: 1.36 + 2.34 = 3.70 EUR per kWh/h)
- [x] 3.2 Rewrite `calculate_route` for (begin country, end country, start, end, FX text): same-country and period checks, one `optimize` per TSO, a `TsoLeg` per TSO; verify route tests for same country, end before start and "No tariff for the dates" (BG->HU from 2025-12-01 names Bulgartransgaz and the point)
- [x] 3.3 Add per-MWh per leg (24 x days for kWh/h, days for kWh/d), EUR/MWh per leg and route totals (None while a needed rate is missing); verify the "Forty-two day period", "Bulgartransgaz per kWh/d" (2.6884), "Route total" (10.0000) and "Over-booked days are not counted" tests
- [x] 3.4 Verify "TSOs choose independently" and "FX rate does not change the choice" (same products at 380 and 420) with hand-made tables

## 4. Capacity fee calculator

- [x] 4.1 Convert capacity per the point's unit (kWh/h: /24, kWh/d: as typed) and price from the point's rows; verify the Gastrans (13,375.00 EUR) and Bulgartransgaz (12,110.85 EUR) quarter tests and that the FGSZ demo is still 1,565,115 HUF
- [x] 4.2 Round totals and invoices in minor units (HUF 0 decimals, EUR 2) reusing `split_by_weights`, and add a currency-aware formatter; verify the EUR cents invoice test (4,080.83 / 3,949.19 / 4,080.83) and the unchanged HUF invoice (527,376 / 510,363 / 527,376)

## 5. App

- [x] 5.1 Rebuild tab 1: "Route beginning" / "Route ending" (HU, RS, BG; default BG -> HU), dates, FX box only when the route touches HU; verify app tests that there is no TSO dropdown and that BG->RS shows no FX box
- [x] 5.2 Show the point table, one segment table per TSO in its own unit, the over-booking note naming the TSO, the Interruptible note, and the summary (per TSO and route, EUR/MWh route rows); verify app tests for the BG->HU point list, HU->BG Interruptible flags and note, and FGSZ/route EUR/MWh missing until a rate is entered
- [x] 5.3 Tab 2: TSO dropdown (FGSZ, Gastrans, Bulgartransgaz) filtering the points, labels with " - Interruptible", metrics and invoice labelled with the point's currency and unit; verify app tests for "Points follow the TSO", the Interruptible labels and "Labels follow the currency"

## 6. Acceptance tests

- [x] 6.1 Rewrite the acceptance tests around corridor routes: every country pair returns a result or a message; impossible requests are messages; the gas-year boundary and open-ended row checks run on a BG->HU route; quarter versus three months flips with the prices; tab 2 invoices sum to the total for every point and instrument of all three TSOs; verify `python -m pytest tests/test_acceptance.py` passes

## 7. Docs

- [x] 7.1 Update the README (overview of the three TSOs, the BG->HU tab 1 demo with figures computed from the sample, a Gastrans or Bulgartransgaz tab 2 example, shape and scope sections) and verify a test that the README demo figures match the app
- [x] 7.2 Record any implementation decisions taken while applying the change in `PLANNING_LOG.md`

## 8. Wrap-up

- [x] 8.1 Run the full test suite (`python -m pytest`) and verify it passes
- [ ] 8.2 Run the app locally on the sample (`python -m streamlit run app.py`) and check all six routes and one point per TSO on tab 2 by eye

## 9. Real export check (user)

- [ ] 9.1 The user runs the app locally against the private real export (`FGSZ_TARIFF_FILE`) and confirms the Gastrans and Bulgartransgaz points load with the expected operator codes, EICs, units and capacity types; the export is never committed or uploaded
