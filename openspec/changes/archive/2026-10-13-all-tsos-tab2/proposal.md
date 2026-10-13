## Why

The app knows only three TSOs (FGSZ, Gastrans, Bulgartransgaz), while the real tariff file, now committed as `data/real/tariffs_real.xlsx`, holds the tariffs of 21 transmission system operators across Central, Eastern and Southern Europe. Traders book capacity at the borders between those TSOs, most often as bundled capacity (the exit of one TSO and the entry of the next booked together), so the Capacity Fee Calculator should price any of those points, bundled or one side at a time. This is the first of two changes: it brings all TSOs into the data layer and tab 2; routing across the whole network on tab 1 follows as a separate change.

## What Changes

- The tariff loader accepts the rows of all 21 TSOs in the real file, each in its own currency (EUR, HUF, RON, CZK or PLN) and capacity unit (kWh/h or kWh/d). The operators EDDGAZ, EgDegel, HEXUM, ISDP, LNGCRO, MFGT, NKM_el and TIGAZ (DSO exits, storage operators, and LNGCRO's single 2022 row) are left out, as are every TSO's storage and production points. Plinacro's pre-euro HRK rows are skipped silently, like Bulgartransgaz's BGN rows. Capacity types other than Firm and Interruptible (GASCADE's DZK) are ignored.
- **BREAKING** The default tariff file becomes the real file `data/real/tariffs_real.xlsx`, both locally and on the hosted app; the synthetic sample stays as the data of the existing tests.
- The point list is built from the tariff data with name-cleaning rules and a small override table, instead of the hand-written list of 30 points. It gives 109 single-side points, 14 LNG terminal entries and 43 bundled border points.
- Bundled points pair the exit of one TSO with the entry of the neighbouring TSO at the same border and flow, and are offered only where both sides are Firm. At Baumgarten only the WAG point is used on the Austrian side; GCA's other Baumgarten point and TAG's Baumgarten points are left out of the app.
- Tab 2 asks first what is booked: a **Bundled** point (one dropdown of bundles), a **Single side** (TSO dropdown, then point dropdown, as today) or an **LNG entry** (one dropdown of terminals).
- A bundled booking shows each side's cost and monthly invoice breakdown in that TSO's own currency and unit. Where a side is not in EUR, a rate box (e.g. HUF per 1 EUR) appears; once every needed rate is typed in, an EUR total for the bundle is shown. Single sides and LNG entries stay without FX.
- TSOs are shown by their full names (e.g. Eustream, Gas Connect Austria, Open Grid Europe, Snam Rete Gas).
- A product whose period crosses a tariff change is priced part by part: most of the new TSOs change their tariffs on 1 January (Eustream also on 1 May), so a gas year, and sometimes a quarter, spans two tariff rows. Each part costs the product's cell of the row valid in it, weighted by its days. This replaces the rule that a product is priced from the row valid on its first day, on both tabs; tab 2's monthly invoice follows the tariff of each month, and its price shows every tariff used.
- Tab 1 otherwise is unchanged: it still prices routes along the HU - RS - BG corridor, now on the real file by default.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `tariff-loading`: the default file becomes the real export; the scope covers the 21 TSOs with their currencies and units; HRK rows are skipped; capacity types other than Firm and Interruptible are ignored; a product crossing a tariff change is priced part by part.
- `route-tariff-calculator`: products are priced part by part across tariff changes (route price, optimisation, cost per MWh), and the Details section lists every tariff row and cell a product used.
- `fgsz-network-points`: the fixed list of 30 points becomes a point catalog built from the data, covering single sides, LNG entries and bundled border points (including the Baumgarten WAG pairing); new label forms for bundles and LNG entries; full TSO names; the corridor topology for tab 1 is unchanged.
- `capacity-fee-calculator`: booking type chosen first; bundled bookings priced per side with per-side invoices; optional EUR total with rate boxes for bundles; rounding to cents for EUR, RON, CZK and PLN; prices and monthly invoices follow each tariff row a product crosses.

## Impact

- Code: `core/tariffs.py` (TSO formats, scope filter, default path), `core/points.py` (catalog built from the data, bundles, names), `core/fee.py` (bundled fee, per-side results, EUR total), `core/money.py` (rounding per currency), `app.py` (tab 2 booking type and rate boxes, default file caption).
- Tests: tests that rely on the default file must pin the synthetic sample explicitly; new tests cover the catalog counts, the bundle pairing, bundled fees and the EUR total on the real file.
- Data: no new data file; the real file already committed becomes the default.
- Docs: README (default data, tab 2 walk-through, TSO list).
- Hosted app (Streamlit Community Cloud) serves the real tariffs after the next deployment.
