## Why

Before a capacity auction, and again once capacity is booked, the TSO asks for a financial guarantee (in practice a bank guarantee). Each TSO has its own rule for its amount, and today it is worked out by hand. A third tab should work out the guarantee for a list of bookings, starting with Eustream, whose rule is in section 7.6.2 of its Operational Order (24 July 2025).

## What Changes

- New third tab, **Bank Guarantee Calculator**, next to the Route Tariff and Capacity Fee tabs.
- Booking inputs:
  - a TSO dropdown (only Eustream for now), and a network point of that TSO (Eustream's single sides);
  - a product instrument and its period, and a requested capacity with its unit, using the same pickers as tab 2;
  - a stage: **Capacity auction** (the guarantee covers the capacity fee only) or **Booked capacity** (it also covers the GfON);
  - for a booked capacity, the CEGHIX in EUR/MWh, typed in, with a note that it is the CEGHIX valid on the day before the booking.
- **Add to list** adds the booking as a row of a table. Rows can be removed and the list cleared, and every row keeps its own stage and CEGHIX. Columns:
  - the inputs: point, product, capacity, stage, CEGHIX;
  - the results: capacity fee, GfON fee, capacity fee guarantee, GfON fee guarantee and total guarantee, all in EUR;
  - a total under the table.
- Eustream rule (Operational Order 7.6.2):
  - The **capacity fee** is tab 2's figure.
  - **GfON** (the neutrality fee) is the volume at full use of the booked capacity (24 hours per gas day), in MWh, times (CEGHIX + 1) × 0.85 / 100 EUR/MWh.
  - For a product longer than two months (gas year, quarter), each guarantee is the two most expensive months.
  - For a month or a day, each guarantee is the whole fee.
  - An auction row shows "–" for CEGHIX, GfON fee and GfON fee guarantee.
- The tariff file, tab 1 and tab 2 do not change.

## Capabilities

### New Capabilities
- `bank-guarantee-calculator`: The Bank Guarantee Calculator tab: its inputs, the list of bookings and its columns, and each supported TSO's rule for the required financial guarantee (Eustream first).

### Modified Capabilities
<!-- None: tab 3 reuses tab 2's capacity fee as it is; capacity-fee-calculator and tariff-loading keep their requirements. -->

## Impact

- **New code:**
  - `core/guarantee.py`, the guarantee rules and GfON, with exact decimals. It reuses `core.fee.calculate_fee` and `core.money`.
  - The new tab in `app.py`. Tab 2's period pickers become a shared helper, so both tabs use one copy.
- **New tests:** `tests/test_guarantee.py`, with hand-worked figures, and app tests for tab 3.
- **Dependencies:** none new. The table's row selection uses Streamlit's `st.dataframe` selection, which the pinned streamlit 1.64.0 has.
- **Not covered:**
  - other TSOs (each will need its own rule);
  - the imbalance guarantee (7.6.3) and amounts set after a credit check (7.6.5);
  - fetching CEGHIX automatically (left for a later change);
  - Eustream's domestic point, which is not in the app's point catalog.
