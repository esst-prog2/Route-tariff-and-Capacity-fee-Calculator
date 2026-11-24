## Context

Tab 3's rules live in `core/guarantee.py` (`GUARANTEE_RULES`, `GUARANTEE_NOTES`, `STAGED_TSOS`); each maps tab 2's `FeeResult`, already raised by the surcharge, to a `GuaranteeResult`. Since `add-fgsz-guarantee` the table is currency-aware: each row is in its own currency and the totals are grouped by currency. The combined EUR row, however, knows only HUF: `guarantee_totals(sums, huf_rate)` and one "HUF per 1 EUR" box. NET4GAS bills in CZK (two decimals), and tab 2 already invoices its gas years and quarters in equal months at the tariff valid in each month (`EQUAL_MONTH_INSTRUMENTS`).

NET4GAS's Annex 1 does not set a deposit per contract. It asks the user to keep its credit exposure (the maximum possible debt less the securities provided) within a credit limit, where the debt is the sum of three risks. Only the first one, the transmission risk (one monthly payment), belongs to a single booking.

## Goals / Non-Goals

**Goals:**
- Add NET4GAS as a fourth rule with no change to any Eustream, GCA or FGSZ figure.
- Make the combined EUR row work for any number of non-EUR currencies.

**Non-Goals:**
- No credit limit input, daily auction risk or balancing-transmission risk (description only, the user's choice).
- No VAT (the user's choice: reverse charge for a Hungarian user).
- No rate box for a currency that is not in the list.

## Decisions

**1. The guarantee is the largest invoice line.** `net4gas_guarantee` takes `max(line.amount for line in result.invoice)`. For a gas year or quarter this is the most expensive month; NET4GAS's tariffs change on 1 January, so a gas year takes a month of the dearer calendar year. A month or a day is invoiced in a single line, so the same expression gives its whole fee. The amounts are the surcharged invoice lines, which already add up to the total. *Alternative:* the first month (like GCA) or total / 12. Rejected by the user in favour of the largest month.

**2. NET4GAS secures only the capacity fee.** GfON, the commodity / volume fee guarantee and VAT stay `None` and show "–" (the variable part, decision 4, is shown but not secured); the total guarantee equals the capacity fee guarantee. NET4GAS stays out of `STAGED_TSOS`, so the stage and CEGHIX are hidden as for GCA and FGSZ.

**3. One rate box per non-EUR currency in the list.** `app.py` loops over the currencies of `guarantee_sums` (EUR, HUF, CZK in `GUARANTEE_CURRENCIES` order). For each non-EUR currency it shows a "<currency> per 1 EUR" box with the key `guar_rate_<currency>` (the HUF key is unchanged) and a placeholder from `RATE_PLACEHOLDERS`; an invalid entry shows `money.rate_message(currency)`. `guarantee_totals(sums, rates)` adds the "All in EUR" row only when every non-EUR currency in the list has a rate, because a total that left out a currency would mislead. Each column is the sum of every currency's total converted with `money.minor_to_major` and divided by its rate, rounded to cents once. The label chains the rates: "All in EUR (1 EUR = 400 HUF = 25 CZK)", which stays "All in EUR (1 EUR = 400 HUF)" for a list without CZK. *Alternative:* convert only the currencies that have a rate. Rejected, because the row would no longer be the whole list.

**4. The variable part is set by `calculate_guarantee`, not by the rule.** The rules keep their `(result, ceghix)` signature. `asks_variable_inputs(point)` is true for a NET4GAS exit point; there `calculate_guarantee` reads `ote_text` and `czk_rate_text` (`parse_ote`, `parse_czk_rate`, messages like the CEGHIX's) and sets `commodity_fee` to `net4gas_variable_fee`: kWh/d × the invoice's days / 1000 × OTE × 0.0009 × rate, rounded to haléře once; the surcharge does not touch it. `net4gas_guarantee` sets `commodity_fee=0`, which stays for an entry point. `commodity_fee_guarantee` stays `None`, so the total guarantee is unchanged. *Alternative:* passing all inputs to every rule. Rejected as a wider change for one TSO.

**5. The per-booking rate is separate from the totals' rate.** The booking's "CZK per 1 EUR (variable part)" box (`guar_czk_rate`) is saved with the row, like the CEGHIX; the totals' "CZK per 1 EUR" box (`guar_rate_CZK`) only converts totals. A rate typed for one booking therefore never re-prices an older row.

**6. Real-file figures.** The spec scenarios use Lanžhot CZ>SK (exit) and SK>CZ (entry), 100,000 kWh/h, as the other TSOs use one point each.

## Risks / Trade-offs

- [The Network Code is dated 7 December 2017; NET4GAS may have changed Annex 1 since] → The description names the version, so a reader can check it.
- [The largest month overstates the guarantee of a booking whose months differ, e.g. Oct–Dec at a lower tariff] → It is the safe side of "the monthly payment", and it is the user's choice.
- [The tab's figure is not the security actually needed: the credit limit lowers it and the other two risks raise it] → The expander says both, in words.
- ["107,705" is read as 107,705: the app takes a comma before three digits as a thousands separator] → The placeholder shows "e.g. 107.705" with a point; the spec states it.
- [With three currencies, the combined row needs two rates] → Each box appears only when its currency is in the list, and the row appears once all of them are filled.
