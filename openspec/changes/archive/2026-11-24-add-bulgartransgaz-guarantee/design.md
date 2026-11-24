## Context

Tab 3's rules live in `core/guarantee.py`; each maps tab 2's `FeeResult`, already raised by the full surcharge, to a `GuaranteeResult`. `GuaranteeResult` already has a `vat` field (FGSZ) that the table shows and the total adds. Bulgartransgaz bills in EUR, and its tariffs are in kWh/d.

## Goals / Non-Goals

**Goals:**
- Add Bulgartransgaz as a fifth rule with no change to any other TSO's figure.
- Support the bundled half-premium of 8.11 without changing the shown capacity fee.

**Non-Goals:**
- No minimum credit limit in the totals (8.2, description only).
- No auction-date tariff (the product's own tariff is used; the user's choice).
- No VAT input (always 20%).

## Decisions

**1. Share, then VAT, each rounded once.** `bulgartransgaz_guarantee` takes the exact product value (`exact_total`, the fee before rounding), multiplies it by `BULGARTRANSGAZ_SHARE` {gas year 6%, quarter 25%, month 70%, day 100%} and rounds to cents; the VAT is 20% of that rounded amount, rounded to cents. The shown parts add up to the total, as for FGSZ. VAT is computed on the major amount (`money.minor_to_major`), since EUR has cents. *Alternative:* round value × share × 1.2 once. Rejected, because the row would not add up.

**2. Bundled is handled in `calculate_guarantee`.** The rules keep their `(result, ceghix)` signature. `calculate_guarantee` gains `bundled=False`; for a point where `asks_bundled(point)` (Bulgartransgaz) and `bundled`, it calls `bulgartransgaz_guarantee(result, counted=with_surcharge(base, surcharge / 2))`, where `base` is the fee before the surcharge. The guarantee is taken from `counted`; the capacity fee and the invoice stay `result`'s. For any other TSO `bundled` is ignored. *Alternative:* subtracting half the premium from the rounded fee. Rejected, because it rounds twice.

**3. The Bundled column.** `app.py` shows "Yes" or "No" for a Bulgartransgaz row and "–" for others, after Surcharge (%), and drops the column when no row is Bulgartransgaz, as with the Eustream-only and NET4GAS exit columns.

**4. Commodity columns only when a row has a commodity fee.** `app.py` drops `COMMODITY_COLUMNS` from both tables when every row's `commodity_fee` is `None` (Eustream, Bulgartransgaz, or a row the tariff file no longer prices). A NET4GAS entry row has a commodity fee of 0, not `None`, so it keeps them, as do GCA and FGSZ rows, whose guarantees include the fee. *Alternative:* hiding them always. Rejected, because GCA's and FGSZ's totals would then include amounts no column shows.

**5. Real-file figures.** The spec scenarios use Kulata/Sidirokastron BG>GR (exit) and GR>BG (entry), 100,000 kWh/h. Bulgartransgaz has no tariff for gas year 2025/26 in the file, so the gas year scenario is 2026/27.

## Risks / Trade-offs

- [A reserve on the product's tariff differs from 8.10's auction-date price when the tariff changes in between] → The user's choice; the description says so.
- [20% VAT although a Hungarian user is reverse-charged] → 8.10 says "including VAT"; the user chose to follow it.
- [The bundled box relies on the user knowing the auction was bundled] → The note names Regulation (EU) 2017/459, and the row shows the choice.
