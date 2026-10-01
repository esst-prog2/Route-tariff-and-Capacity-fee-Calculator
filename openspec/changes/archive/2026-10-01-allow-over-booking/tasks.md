## 1. Optimiser

- [x] 1.1 Price every touched month as min(monthly, daily prices of its requested days) and every touched quarter as min(quarterly, its touched months), and verify optimiser tests for partial months and quarters, ties and the "never dearer than exact cover" check
- [x] 1.2 Skip a monthly or quarterly product whose first day has no tariff (`PriceUnavailable`, extended by `NoTariffError`) and verify a route test with tariffs starting on 2026-10-15
- [x] 1.3 Count over-booked days per segment and per plan, and verify the Q4-minus-edge-days route test (2 days outside, 90 requested days for per-MWh)

## 2. App

- [x] 2.1 Show the product's own dates, a "Days outside period" column and an over-booking note, and verify an app test on the sample: 2026-10-02..2026-12-30 shows one quarterly segment at 2052.1344 HUF per kWh/h

## 3. Docs

- [x] 3.1 Update the README to describe over-booking and verify the demo figures are unchanged (4134.1287 HUF per kWh/h for 2026-10-01..2027-03-31)
- [x] 3.2 Record the decisions in `PLANNING_LOG.md`
- [x] 3.3 Run the full test suite and verify it passes
