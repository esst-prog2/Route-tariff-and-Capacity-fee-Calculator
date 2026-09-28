## Purpose

Defines the fixed list of FGSZ cross-border points the MVP offers, how each is identified in the tariff data, and how it is labelled in the UI. Both calculator tabs share this single list.

## ADDED Requirements

### Requirement: Supported points
The system SHALL offer exactly these FGSZ cross-border points, identified by EIC and direction, and no others (storage and production entries and the domestic exit sum are excluded):

| Direction | Cleaned name | EIC |
|---|---|---|
| Entry | Mosonmagyaróvár (AT>HU) | 21Z000000000003C |
| Entry | Beregdaróc (UA>HU) | 21Z000000000139O |
| Entry | Csanádpalota (RO>HU) | 21Z000000000236Q |
| Entry | Drávaszerdahely (CR>HU) | 21Z000000000249H |
| Entry | Balassagyarmat (SK>HU) | 21Z000000000358C |
| Entry | Kiskundorozsma 2 (RS>HU) | 21Z000000000505P |
| Entry | VIP Bereg (UA>HU) | 21Z000000000507L |
| Exit | Balassagyarmat (HU>SK) | 21Z000000000358C |
| Exit | Csanádpalota (HU>RO) | 21Z000000000236Q |
| Exit | Drávaszerdahely (HU>CR) | 21Z000000000249H |
| Exit | Kiskundorozsma (HU>RS) | 21Z000000000154S |
| Exit | VIP Bereg (HU>UA) | 21Z000000000507L |

#### Scenario: Excluded points are not offered
- **WHEN** the point lists are shown
- **THEN** Egyesített Kitárolás, UGS-2-SZOREG, MOL Nyrt KTD, Méhkerék "0" pont, the `n.a` exit and any point that has only Interruptible rows are absent

### Requirement: Point identity
The system SHALL identify a point in the tariff data by its EIC together with its direction, not by the raw `Network point` text, so that differently spelled source names for the same point resolve to the same point.

#### Scenario: Two source names, one EIC
- **WHEN** the source contains `Balassagyarmat/Velké Zlievce - HU (SK>HU)` (Entry) and `Balassagyarmat (HU>SK) MGT` (Exit), both with EIC 21Z000000000358C
- **THEN** the first resolves to the entry "Balassagyarmat (SK>HU)" and the second to the exit "Balassagyarmat (HU>SK)", regardless of how the source spells the names

#### Scenario: Look-alike names with different EICs
- **WHEN** the source contains `Kiskundorozsma - HU (HU>RS)` (EIC 21Z000000000154S) and `Kiskundorozsma 2 - HU (RS>HU)` (EIC 21Z000000000505P)
- **THEN** they resolve to two different points

### Requirement: Point labels
Dropdown labels SHALL use the form "cleaned name (EIC)". On the Capacity Fee Calculator, where entries and exits share one list, the label SHALL include the direction so that all 12 labels are unique, for example "Csanádpalota RO>HU (21Z000000000236Q)" and "Csanádpalota HU>RO (21Z000000000236Q)". On the Route Tariff Calculator the entry and exit dropdowns are separate, so their labels SHALL use the cleaned name and EIC.

#### Scenario: Unique labels on tab 2
- **WHEN** the tab 2 point dropdown is shown
- **THEN** it has 12 distinct labels, and the four points that exist as both entry and exit each appear twice with different directions

### Requirement: TSO selection
Both tabs SHALL show a TSO dropdown. In the MVP it SHALL contain only FGSZ, and the point lists SHALL be those of the selected TSO.

#### Scenario: Single TSO
- **WHEN** either tab is opened
- **THEN** the TSO dropdown offers only FGSZ
