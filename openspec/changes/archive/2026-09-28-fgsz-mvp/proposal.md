## Why

Traders in the system usage department need the capacity-booking cost of a gas route quickly and clearly. Today this is calculated by hand from tariff exports, which is slow and error-prone. A first useful version scoped to a single TSO (FGSZ, Hungary) proves the calculation logic and the UI end to end before other TSOs, whose tariff rules may differ, are added.

## What Changes

- Add a Python + Streamlit application with a UI-independent, unit-testable `core/` package (tariff loading, route optimizer, fee calculator).
- Load the tariff Excel export (wide format: one row per point, direction, capacity type and validity window, with `Year`, `Q*`, `M_*`, `D_*` price columns) into a queryable structure, filtered to FGSZ and Firm capacity.
- Offer a fixed list of 12 FGSZ cross-border points (7 entries, 5 exits) with cleaned labels in the form "name (EIC)".
- **Tab 1, Route Tariff Calculator:** entry point + exit point + booking period give the cheapest combination of quarterly, monthly and daily products, summed over entry and exit, shown per segment with a "Tariff used" column, an all-daily baseline and the saving, and totals in HUF per kWh/h, HUF/MWh and EUR/MWh (from a trader-typed FX rate).
- **Tab 2, Capacity Fee Calculator:** point + product instrument (gas year, quarter, month or day) + capacity in kWh/d give the total cost in HUF and a monthly invoice breakdown that sums exactly to the total.
- Reject impossible requests (wrong entry/exit pair, no tariff for the dates, invalid dates) with a message instead of a crash.
- Read the tariff file from a configured path (default: a committed synthetic sample) with an optional in-UI uploader; keep the real export out of git.

Out of scope for this change: other TSOs, Interruptible capacity, storage/production points and the domestic exit sum, yearly products in the tab 1 optimizer, within-day products, live API integrations, real-time FX, financial-security calculation, and multi-TSO routes.

## Capabilities

### New Capabilities
- `tariff-loading`: reading and validating the tariff file, filtering to FGSZ Firm rows, and looking up the row valid on a given date.
- `fgsz-network-points`: the fixed list of 12 border points, their cleaned labels and their entry/exit direction.
- `route-tariff-calculator`: tab 1, the cheapest quarterly/monthly/daily combination for an entry-exit route over a booking period, and its presentation.
- `capacity-fee-calculator`: tab 2, the fee for a chosen product instrument and capacity, and its monthly invoice breakdown.

### Modified Capabilities
<!-- None: the project has no existing specs. -->

## Impact

- New code: a `core/` package, a Streamlit app, unit tests and a synthetic sample tariff file under `data/sample/`.
- New config: tariff file path (environment variable or setting) and a `.gitignore` for the private real export.
- Dependencies: Python, Streamlit, pandas, openpyxl.
- No existing code or APIs are affected.
