## Why

The teacher's review showed that the Route Tariff Calculator only covers the requested period exactly: it never buys a product longer than the request, so 2026-10-02 to 2026-12-30 costs 3040.5 HUF per kWh/h while booking the whole of Q4 costs 2052.1 (48 % more), and 2 to 28 November costs 1012.1 against 819.2 for plain November. The README and the app both promise the "cheapest combination". A spike over 30 realistic periods on all 35 entry x exit pairs of the synthetic sample measured a median overpay of 0.0 % but a worst case of 135.8 %, with 428 of 1050 cases overpaying (median 35.3 % among those), almost all of them periods that miss a few edge days of a month or quarter.

## What Changes

- The tab 1 optimiser may **over-book**: a monthly or quarterly product may cover days outside the requested period when that is the cheapest way to cover every requested day. Partly covered months and quarters are no longer forced to daily or monthly products.
- A monthly or quarterly product that starts before the period and has no tariff on its first day is simply not an option (no error).
- The results table shows each product's own dates and a new "Days outside period" column, and a note appears when the plan over-books.
- Unchanged: the all-daily baseline and the HUF/MWh and EUR/MWh figures use the requested days only; yearly products stay excluded; ties still prefer the coarser product.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `route-tariff-calculator`: the Optimization rules allow over-booking, the Results panel shows over-booked days, and Cost per MWh states that it uses the requested days only.

## Impact

- Code: `core/optimizer.py` (new rules, `PriceUnavailable`, over-booked-day counts), `core/route.py` (`NoTariffError` becomes a `PriceUnavailable`), `app.py` (new column and note).
- Tests: optimiser, route and app tests updated for the new rules.
- Docs: README describes over-booking; `PLANNING_LOG.md` records the decisions.
