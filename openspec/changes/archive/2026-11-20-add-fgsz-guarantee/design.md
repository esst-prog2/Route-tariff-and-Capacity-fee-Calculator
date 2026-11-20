## Context

Tab 3's guarantee rules live in `core/guarantee.py` (`GUARANTEE_RULES`, `GUARANTEE_NOTES`, `STAGED_TSOS`). Each rule maps a `FeeResult` (tab 2's fee, already raised by the surcharge) to a `GuaranteeResult`. `app.py` turns the result into one table row through the `GUARANTEE_AMOUNTS` column-to-field mapping and adds a single total row. Two things stand in FGSZ's way:
- `calculate_guarantee` raises `ValueError` for a non-EUR fee, because the table assumes EUR.
- The total row sums every row as EUR cents.

`money` already handles HUF (`CURRENCY_DECIMALS`, whole forints, `round_minor` halves away from zero, `format_amount`) and typed exchange rates (`parse_fx_rate`, `rate_message`), as tabs 1 and 2 use them.

## Goals / Non-Goals

**Goals:**
- Add FGSZ as a third rule with no change to any Eustream or GCA figure.
- Make the table currency-aware once, so that any later TSO in another currency needs no further UI work.

**Non-Goals:**
- No risk class, auction-stage locking, minimum guarantee or auction security amounts (description only).
- No odourisation fee, no VAT input, no dated volume fee or k (one value for every date, the user's choice).
- No currency conversion inside a row; only the optional combined EUR total.

## Decisions

**1. The FGSZ constants sit next to the rule.** These are `FGSZ_VOLUME_FEE = 29.22` HUF/MWh, `FGSZ_K = 0.8005` and `FGSZ_VAT = 0.27`, each with a comment naming GTC 4.d (1 October 2026) and that the user supplied the fee and k. They are constants rather than a dated table, because the user chose one value for all dates; a later rate change can turn them into a table like `GCA_COMMODITY_RATES`. *Alternative:* a dated table now, rejected as unused structure.

**2. `GuaranteeResult` gains `vat: int | None`; FGSZ reuses the commodity fields.** The volume fee goes into `commodity_fee` and its share into `commodity_fee_guarantee`, so the renamed "Commodity / volume" columns map to the same fields as before. `total_guarantee` adds `vat`. *Alternative:* separate `volume_fee` fields, rejected because the user chose shared columns and the fields would only duplicate the commodity ones.

**3. The shares are exact fractions of the product totals.** `fgsz_guarantee` uses K+A = `result.total` (whole forints, after the surcharge), the capacity part = `round_minor(K × share)` with share {gas year 1/12, quarter 1/3, month 1, day 1}, F = capacity_kwh_d × days / 1000 × 29.22 (exit) or 0 (entry), the volume part = `round_minor(F × vol_share × k)` with vol_share {2/12, 2/3, 1, 1}, and VAT = `round_minor((capacity part + volume part) × 0.27)`. Each displayed part is rounded once, and the total is the sum of the shown parts, so a row always adds up. The days are taken from the invoice lines (the sum of `line.days`), as for GCA. *Alternative:* round only the final B. Rejected, because the parts shown would then not add up to the total.

**4. Currency comes from the result, totals are grouped by it.** `calculate_guarantee` no longer refuses non-EUR fees. The app adds a "Currency" column from `result.currency` and formats each amount with `money.format_amount(amount, row currency)`. `guarantee_totals(results)` returns one row per currency (EUR first, then HUF, in `money`'s currency order), each summing the `GUARANTEE_AMOUNTS` fields of that currency's rows. When a HUF row exists, a "HUF per 1 EUR" `text_input` (key `guar_rate_HUF`) appears under the total table. A valid rate adds the "All in EUR (1 EUR = <rate> HUF)" row; each of its columns is computed exactly as the EUR cents / 100 plus the HUF forints / rate, then rounded to cents. *Alternative:* one total row with a currency per cell. Rejected, because it is unreadable and impossible to sort.

**5. FGSZ is unstaged.** It stays out of `STAGED_TSOS`, so the existing GCA path hides the stage and CEGHIX and stores `stage=None`. The surcharge path is shared.

## Risks / Trade-offs

- [The volume fee and k are typed constants that FGSZ changes each gas year] → They are in one place with their source, and the FGSZ description names them, so a stale value is visible.
- [Using the 2026 formula and values for earlier bookings misstates their real guarantee] → This is the user's explicit choice and is stated in the spec; the description says which values are used.
- [Renaming the commodity columns and adding Currency and VAT columns changes every existing tab 3 table assertion] → Expected; the column test and the row assertions are updated in one task, and the amounts in Eustream and GCA rows stay unchanged.
- [A wide table (16 columns)] → Streamlit's dataframe scrolls horizontally, as the 14-column table already does. The left-hand columns keep the row's identity in view.
- [Rounding each part once can differ by a forint from rounding B once] → Chosen so that the row adds up; the difference is at most 2 HUF and is stated in the design.
