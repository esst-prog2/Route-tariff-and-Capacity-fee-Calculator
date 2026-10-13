## MODIFIED Requirements

### Requirement: Supported points
The system SHALL offer exactly these cross-border points of three TSOs, identified by TSO, EIC and direction, and no others (storage and production entries, such as UGS Chiren and the FGSZ storage points, and the FGSZ domestic exit sum are excluded). The capacity type is the one the scope filter gives the point (Firm when the point has Firm rows, otherwise Interruptible); in the data used for this change it is:

| TSO | Direction | Cleaned name (flow) | EIC | Capacity type |
|---|---|---|---|---|
| FGSZ | Entry | Mosonmagyaróvár (AT>HU) | 21Z000000000003C | Firm |
| FGSZ | Entry | Beregdaróc (UA>HU) | 21Z000000000139O | Firm |
| FGSZ | Entry | Csanádpalota (RO>HU) | 21Z000000000236Q | Firm |
| FGSZ | Entry | Drávaszerdahely (CR>HU) | 21Z000000000249H | Firm |
| FGSZ | Entry | Balassagyarmat (SK>HU) | 21Z000000000358C | Firm |
| FGSZ | Entry | Kiskundorozsma 2 (RS>HU) | 21Z000000000505P | Firm |
| FGSZ | Entry | VIP Bereg (UA>HU) | 21Z000000000507L | Firm |
| FGSZ | Exit | Balassagyarmat (HU>SK) | 21Z000000000358C | Firm |
| FGSZ | Exit | Csanádpalota (HU>RO) | 21Z000000000236Q | Firm |
| FGSZ | Exit | Drávaszerdahely (HU>CR) | 21Z000000000249H | Firm |
| FGSZ | Exit | Kiskundorozsma (HU>RS) | 21Z000000000154S | Firm |
| FGSZ | Exit | Kiskundorozsma 2 (HU>RS) | 21Z000000000505P | Interruptible |
| FGSZ | Exit | VIP Bereg (HU>UA) | 21Z000000000507L | Firm |
| Gastrans | Entry | Kireevo/Zaychar (BG>RS) | 58Z-000000007-KZ | Firm |
| Gastrans | Entry | Kiskundorozsma 2 (HU>RS) | 21Z000000000505P | Interruptible |
| Gastrans | Exit | Kiskundorozsma 2 (RS>HU) | 21Z000000000505P | Firm |
| Gastrans | Exit | Kireevo/Zaychar (RS>BG) | 58Z-000000007-KZ | Interruptible |
| Bulgartransgaz | Entry | Kireevo/Zaychar (RS>BG) | 58Z-000000007-KZ | Firm |
| Bulgartransgaz | Entry | Kulata/Sidirokastron (GR>BG) | 21Z000000000020C | Firm |
| Bulgartransgaz | Entry | Strandzha 1/Malkoclar (TR>BG) | 21Z000000000157M | Firm |
| Bulgartransgaz | Entry | Negru Voda 1/Kardam (RO>BG) | 21Z000000000159I | Firm |
| Bulgartransgaz | Entry | Ruse/Giurgiu (RO>BG) | 21Z0000000002798 | Firm |
| Bulgartransgaz | Entry | Strandzha 2/Malkoclar (TR>BG) | 58Z-00000015-S2M | Firm |
| Bulgartransgaz | Entry | Stara Zagora (ICGB>BG) | 58Z-IP-00034-STZ | Firm |
| Bulgartransgaz | Exit | Kireevo/Zaychar (BG>RS) | 58Z-000000007-KZ | Firm |
| Bulgartransgaz | Exit | Kulata/Sidirokastron (BG>GR) | 21Z000000000020C | Firm |
| Bulgartransgaz | Exit | Kyustendil/Zidilovo (BG>MK) | 21Z000000000137S | Firm |
| Bulgartransgaz | Exit | Strandzha 1/Malkoclar (BG>TR) | 21Z000000000157M | Firm |
| Bulgartransgaz | Exit | Negru Voda 1/Kardam (BG>RO) | 21Z000000000159I | Firm |
| Bulgartransgaz | Exit | Ruse/Giurgiu (BG>RO) | 21Z0000000002798 | Firm |

The TSOs are shown as FGSZ, Gastrans and Bulgartransgaz; in the tariff file they are `FGSZ`, `Gastran` and `BGTRGAZ`.

#### Scenario: Excluded points are not offered
- **WHEN** the point lists are shown
- **THEN** Egyesített Kitárolás, UGS-2-SZOREG, MOL Nyrt KTD, Méhkerék "0" pont, the FGSZ `n.a` exit and UGS Chiren are absent

#### Scenario: Point counts per TSO
- **WHEN** the point lists are shown
- **THEN** FGSZ has 13 points, Gastrans 4 and Bulgartransgaz 13

### Requirement: Point identity
The system SHALL identify a point in the tariff data by its TSO, its EIC and its direction, not by the raw `Network point` text, so that differently spelled source names for the same point resolve to the same point, and the two sides of a border, which share an EIC, resolve to two different points.

#### Scenario: Two source names, one EIC
- **WHEN** the source contains `Balassagyarmat/Velké Zlievce - HU (SK>HU)` (Entry) and `Balassagyarmat (HU>SK) MGT` (Exit), both FGSZ with EIC 21Z000000000358C
- **THEN** the first resolves to the entry "Balassagyarmat (SK>HU)" and the second to the exit "Balassagyarmat (HU>SK)", regardless of how the source spells the names

#### Scenario: Look-alike names with different EICs
- **WHEN** the source contains `Kiskundorozsma - HU (HU>RS)` (EIC 21Z000000000154S) and `Kiskundorozsma 2 - HU (RS>HU)` (EIC 21Z000000000505P)
- **THEN** they resolve to two different points

#### Scenario: Two sides of one border
- **WHEN** the source contains the Gastrans exit `Kiskundorozsma 2 - RS (RS>HU)` and the FGSZ entry `Kiskundorozsma 2 - HU (RS>HU)`, both with EIC 21Z000000000505P
- **THEN** they resolve to two different points, one of each TSO

### Requirement: Point labels
On the Capacity Fee Calculator, point labels SHALL use the form "cleaned name flow (EIC)", for example "Csanádpalota RO>HU (21Z000000000236Q)", so that all labels of one TSO are unique; a point that uses Interruptible capacity SHALL have " - Interruptible" appended, for example "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible". On the Route Tariff Calculator each listed point SHALL show its TSO, its cleaned name with flow, its EIC, its direction and its capacity type in separate columns.

#### Scenario: Unique labels on tab 2
- **WHEN** the tab 2 point dropdown is shown for FGSZ
- **THEN** it has 13 distinct labels, and the points that exist as both entry and exit appear twice with different flows

#### Scenario: Interruptible label
- **WHEN** the tab 2 point dropdown is shown for Gastrans
- **THEN** the labels of Kiskundorozsma 2 (HU>RS) and Kireevo/Zaychar (RS>BG) end with " - Interruptible" and the other two do not

## ADDED Requirements

### Requirement: TSO dropdown
The Capacity Fee Calculator SHALL show a TSO dropdown offering FGSZ, Gastrans and Bulgartransgaz, and its point list SHALL be the points of the selected TSO. The Route Tariff Calculator SHALL NOT have a TSO dropdown; the TSOs on a route follow from its beginning and ending countries.

#### Scenario: Three TSOs on tab 2
- **WHEN** tab 2 is opened
- **THEN** the TSO dropdown offers FGSZ, Gastrans and Bulgartransgaz, and choosing Bulgartransgaz shows its 13 points

#### Scenario: No TSO dropdown on tab 1
- **WHEN** tab 1 is opened
- **THEN** it has no TSO dropdown

### Requirement: Corridor topology
The system SHALL know the HU - RS - BG corridor as three countries in this order, each with one TSO (HU: FGSZ, RS: Gastrans, BG: Bulgartransgaz), and two borders: HU - RS at Kiskundorozsma 2 (EIC 21Z000000000505P) and RS - BG at Kireevo/Zaychar (EIC 58Z-000000007-KZ). Crossing a border from country X to country Y SHALL use X's TSO's exit with flow X>Y and Y's TSO's entry with flow X>Y at that border.

#### Scenario: Crossing from RS to HU
- **WHEN** gas crosses the HU - RS border from RS to HU
- **THEN** the points used are the Gastrans exit Kiskundorozsma 2 (RS>HU) and the FGSZ entry Kiskundorozsma 2 (RS>HU)

#### Scenario: Crossing from HU to RS
- **WHEN** gas crosses the HU - RS border from HU to RS
- **THEN** the points used are the FGSZ exit Kiskundorozsma 2 (HU>RS) and the Gastrans entry Kiskundorozsma 2 (HU>RS), both Interruptible, and not the FGSZ exit Kiskundorozsma (HU>RS, EIC 21Z000000000154S)

## REMOVED Requirements

### Requirement: TSO selection
**Reason**: It required a TSO dropdown on both tabs containing only FGSZ; tab 1 no longer has a TSO dropdown and tab 2 now offers three TSOs.
**Migration**: Replaced by "TSO dropdown" (three TSOs on tab 2, none on tab 1).
