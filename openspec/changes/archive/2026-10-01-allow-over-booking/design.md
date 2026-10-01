## Context

The optimiser priced full months as min(monthly, dailies), full quarters as min(quarterly, its three months), and partial months day by day. Calendar products nest (day inside month inside quarter), so the cheapest cover that may extend outside the period is still found bottom-up, one calendar unit at a time.

## Decisions

- **Rules.** For every calendar month the period touches: cost = min(monthly price, daily prices of the requested days in it). For every calendar quarter the period touches: cost = min(quarterly price, sum of its touched months' costs). This is exact (the cheapest possible cover from these products) because the products nest; no search over combinations is needed.
- **Ties** prefer the coarser product, as before: at equal cost the trader gets more capacity days.
- **Missing prices.** A product is priced from the row valid on its first day. When that day is before the requested period and no row applies, the product is skipped (`PriceUnavailable`, which `NoTariffError` now extends). A missing tariff on a requested day is still reported to the user.
- **Per-MWh figures** stay divided by the requested days: the trader needs capacity only for those days, so over-booked days are cost without carried energy.
- **Display.** A segment shows the product's own dates; the "Days outside period" column and a note make over-booking visible.

## Risks / Trade-offs

- Over-booked capacity is paid for but unused; that is intended, since it is still cheaper. A trader who must not hold capacity outside the period has no switch to turn it off in this change.
