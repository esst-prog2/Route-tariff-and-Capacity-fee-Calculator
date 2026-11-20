## Why

Tab 3 prices the guarantee for Eustream and Gas Connect Austria, but most routes in the app end at or pass through FGSZ, whose contractual security follows its own formula in chapter 7 of the General Terms and Conditions for Network Usage Contracts (GTC 4.d, applicable as of 1 October 2026). FGSZ bills in HUF, which tab 3 cannot show yet.

## What Changes

- The TSO dropdown on tab 3 offers FGSZ after Eustream and Gas Connect Austria, with FGSZ's 14 interconnection points. Like GCA, FGSZ hides the stage and CEGHIX inputs and keeps the auction surcharge.
- FGSZ's contractual security (GTC 4.d 7.5), in whole forints, always with 27% VAT:
  - gas year: ((K+A) × 1/12 + 2 × F × 1/12 × k) × 1.27
  - quarter: ((K+A) × 1/3 + 2 × F × 1/3 × k) × 1.27
  - month or day: (K+A + F × k) × 1.27
  - K+A is tab 2's capacity fee including the auction surcharge; F is the volume fee on the volume at full use of the capacity (29.22 HUF/MWh) at exit points and 0 at entry points; k = 80.05%. The same values apply to every date, also before 1 October 2026.
- **Multi-currency table:** each row is in its TSO's currency, in a new "Currency" column; the total table has one row per currency; an optional "HUF per 1 EUR" box adds a combined EUR total row.
- The GCA commodity columns are renamed "Commodity / volume fee" and "Commodity / volume fee guarantee" and also carry FGSZ's volume fee; a new "VAT" column shows FGSZ's 27%.
- A closed expander "How FGSZ calculates the financial guarantee" describes 7.5 and, in words only, the HUF 10,000,000 minimum guarantee (7.2), the HUF 35,000,000 auction security and the risk classes (7.4), the deadlines and validity, the forms (7.1), and that additional security (7.3) is not included.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `bank-guarantee-calculator`: the TSO dropdown gains FGSZ; the table gains the Currency and VAT columns, renames the commodity columns and totals per currency with an optional EUR conversion; FGSZ's contractual security rule and its description are added.

## Impact

- `core/guarantee.py`: an FGSZ rule and note; guarantee results in HUF are no longer refused; a VAT amount on the result.
- `app.py` (tab 3): Currency and VAT columns, renamed commodity columns, per-currency totals, the HUF per EUR box and the combined EUR row.
- Tests: `tests/test_guarantee.py` (FGSZ rule) and `tests/test_app.py` (the TSO dropdown, the column list and total rows of the existing tests, the new FGSZ rows).
- `README.md` and the promo page (`docs/index.html`) name FGSZ on tab 3.
- No change to tabs 1 and 2, the tariff file or the Excel workbook.
