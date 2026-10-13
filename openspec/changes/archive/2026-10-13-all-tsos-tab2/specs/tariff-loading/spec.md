## MODIFIED Requirements

### Requirement: Tariff file source
The system SHALL read the tariff file from a configured path, whose default is the committed real tariff file `data/real/tariffs_real.xlsx`. The system SHALL let the user override the file for the current session with an in-UI file uploader. The system SHALL NOT contain tariff prices in its code.

#### Scenario: Default file
- **WHEN** the application starts and no path is configured
- **THEN** the real tariff file `data/real/tariffs_real.xlsx` is loaded

#### Scenario: Configured private file
- **WHEN** the configured path points at another tariff file with the same columns, such as the synthetic sample `data/sample/tariffs_sample.xlsx`
- **THEN** that file is loaded and its prices are used for all calculations

#### Scenario: Uploaded file
- **WHEN** the user uploads a tariff file in the UI
- **THEN** that file replaces the configured file for the rest of the session only

### Requirement: Currency and unit check
The system SHALL expect each TSO's rows in that TSO's own currency and capacity unit, and SHALL NOT convert currencies or units while loading:

| TSO (`System operator`) | Currency | Measure unit |
|---|---|---|
| Amber Grid (`AMBERGR`) | EUR | kWh/h |
| Bulgartransgaz (`BGTRGAZ`) | EUR | kWh/d |
| DESFA (`DESFA`) | EUR | kWh/h |
| Eustream (`EUSTR`) | EUR | kWh/h |
| FGSZ (`FGSZ`) | HUF | kWh/h |
| GASCADE (`GASCADE`) | EUR | kWh/h |
| GAZ-SYSTEM (`GAZSYS`) | PLN | kWh/h |
| Gas Connect Austria (`GCA`) | EUR | kWh/h |
| Gasunie Transport Services (`GTS`) | EUR | kWh/h |
| Gastrans (`Gastran`) | EUR | kWh/h |
| Gasunie Deutschland (`Gasunie`) | EUR | kWh/h |
| ICGB (`ICGB`) | EUR | kWh/d |
| NET4GAS (`NET4GAS`) | CZK | kWh/h |
| Open Grid Europe (`OGE`) | EUR | kWh/h |
| Plinovodi (`Plinovo`) | EUR | kWh/h |
| Trans Austria Gasleitung (`TAG`) | EUR | kWh/h |
| Trans Adriatic Pipeline (`TAP`) | EUR | kWh/d |
| Transgaz (`TRANSGA`) | RON | kWh/h |
| Gas TSO of Ukraine (`UKRTRAG`) | EUR | kWh/d |
| Plinacro (`plinacr`) | EUR | kWh/d |
| Snam Rete Gas (`snam`) | EUR | kWh/h |

Bulgartransgaz rows in BGN and Plinacro rows in HRK SHALL be skipped silently as out of scope (pre-euro tariffs): they are not used and not reported. Any other in-scope row whose currency or unit differs from its TSO's SHALL be excluded, and the message SHALL name the row and the unsupported value.

#### Scenario: Bulgartransgaz BGN rows skipped silently
- **WHEN** the file has Bulgartransgaz rows in BGN valid up to 2025-12-31 and rows in EUR valid from 2026-01-01
- **THEN** only the EUR rows are used, and no excluded-row message mentions the BGN rows

#### Scenario: Plinacro HRK rows skipped silently
- **WHEN** the file has Plinacro rows in HRK (in kWh/h or kWh/d) valid up to 2024 and rows in EUR per kWh/d valid from 2025-01-01
- **THEN** only the EUR rows are used, and no excluded-row message mentions the HRK rows

#### Scenario: Unsupported currency
- **WHEN** an in-scope FGSZ row has currency EUR
- **THEN** the row is excluded and reported, and the rest of the file is still used

#### Scenario: Unexpected unit
- **WHEN** an in-scope Gastrans row has the unit kWh/d
- **THEN** the row is excluded and reported, and the rest of the file is still used

### Requirement: Scope filter
The system SHALL use only rows whose `System operator` is one of the 21 TSOs listed under "Currency and unit check" and whose `Direction` is `Entry` or `Exit`. Rows of any other operator, including EDDGAZ, EgDegel, HEXUM, ISDP, LNGCRO, MFGT, NKM_el and TIGAZ, SHALL be ignored without a message. Only the capacity types `Firm` and `Interruptible` SHALL be used; rows of any other capacity type (such as GASCADE's `DZK`) SHALL be ignored without a message. For each point (TSO, EIC and direction), the system SHALL use the point's `Firm` rows when it has any, and its `Interruptible` rows only when it has no `Firm` row; Firm and Interruptible rows of one point SHALL never be mixed. All other rows, and all within-day (`WD_*`) columns, SHALL be ignored.

#### Scenario: Interruptible rows ignored
- **WHEN** a point has both a Firm and an Interruptible row valid on the same date
- **THEN** only the Firm row is ever used

#### Scenario: Interruptible used where Firm is missing
- **WHEN** the Gastrans exit at Kireevo/Zaychar (RS>BG, EIC 58Z-000000007-KZ) has only Interruptible rows
- **THEN** its Interruptible rows are used, and the point is reported as Interruptible

#### Scenario: Excluded operators ignored
- **WHEN** the real tariff file is loaded
- **THEN** no row of EDDGAZ, EgDegel, HEXUM, ISDP, LNGCRO, MFGT, NKM_el or TIGAZ is used, and none of them is mentioned in any message

#### Scenario: Other capacity types ignored
- **WHEN** GASCADE's VIP Brandov entry has both `Firm` and `DZK` rows
- **THEN** only the Firm rows are used, and the DZK rows are not reported

### Requirement: Price-cell meaning
The system SHALL treat each price cell as the price, in the row's currency, of booking 1 unit of capacity in the row's measure unit (1 kWh/h, or 1 kWh/d for the TSOs priced per kWh/d) for the whole product period (the gas year for `Year`, the calendar quarter for `Q*`, the calendar month for `M_*`, one day for `D_*`), so that the cost for C units of capacity is C x the cell. The month and quarter columns SHALL be mapped to calendar months and quarters regardless of the Hungarian month abbreviations used in the headers (for example `M_Maj` is May).

A point's price for a product SHALL be taken part by part when the product's period crosses a tariff change (for example a gas year at a TSO whose tariffs change on 1 January, or a quarter at a TSO whose tariffs change on 1 May): the period is split where the applicable row changes, and each part costs the product's cell of the row valid in that part x the part's days / the product period's days. With one row for the whole period this is the cell itself. If any day of the product period has no applicable row, the point has no price for that product.

#### Scenario: Month column mapping
- **WHEN** the price for May is requested
- **THEN** the `M_Maj` value is used

#### Scenario: Bulgartransgaz cell per kWh/d
- **WHEN** a Bulgartransgaz `Year` cell is 0.981251 EUR with unit kWh/d
- **THEN** booking 50,000 kWh/d for that gas year costs 50,000 x 0.981251 = 49,062.55 EUR

#### Scenario: Other currency per kWh/h
- **WHEN** a Transgaz `Q4_Oct` cell is 11.892288 RON with unit kWh/h
- **THEN** booking 2,000 kWh/h for that quarter costs 2,000 x 11.892288 = 23,784.576 RON before rounding

#### Scenario: Gas year across a 1 January tariff change
- **WHEN** a point's `Year` cell is 3.97 in the row valid from 2026-01-01 to 2026-12-31 and 4.10 in the row valid from 2027-01-01, and the price of gas year 2026/27 (365 days) is requested
- **THEN** the price is 3.97 x 92/365 + 4.10 x 273/365 = 4.067233 (to six decimals)

#### Scenario: Quarter across a mid-quarter tariff change
- **WHEN** a point's `Q2_Apr` cell is 1.20 in the row valid to 2026-04-30 and 1.32 in the row valid from 2026-05-01, and the price of 2026 Q2 (91 days) is requested
- **THEN** the price is 1.20 x 30/91 + 1.32 x 61/91

#### Scenario: Product with one row
- **WHEN** one row applies on every day of the product period
- **THEN** the price is that row's cell, unchanged
