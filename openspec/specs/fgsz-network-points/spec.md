# fgsz-network-points Specification

## Purpose

Defines the point catalog built from the tariff data (single sides, LNG entries and bundled border points of the 21 TSOs), how each point is identified in the tariff data and labelled in the UI, and the network of border crossings the Route Tariff Calculator's routes run on.

## Requirements

### Requirement: Supported points
The system SHALL build its point catalog from the loaded tariff rows of the 21 TSOs in scope (see tariff-loading), one point per TSO, EIC and direction, with the capacity type the scope filter gives the point (Firm when the point has Firm rows, otherwise Interruptible). The catalog SHALL leave out storage and production points, domestic points and sums, and the Baumgarten points other than the WAG point: FGSZ's Egyesített Kitárolás, UGS-2-SZOREG, MOL Nyrt KTD, Méhkerék "0" pont and the `n.a` exit sum, Bulgartransgaz's UGS Chiren, Eustream's "Domestic" entry and exit, Gas Connect Austria's Baumgarten point with EIC 21Z0000000000600 (including the virtual AT->SK exit) and Trans Austria Gasleitung's Baumgarten points with EIC 21Z000000000164P. Every other point is offered: an entry whose gas comes from an LNG terminal is an LNG entry, and every other point is a single side. On the real tariff file the catalog SHALL have 109 single sides and 14 LNG entries.

The TSOs SHALL be shown by the names given in the tariff-loading "Currency and unit check" table (for example Eustream for `EUSTR` and Gas Connect Austria for `GCA`).

#### Scenario: Excluded points are not offered
- **WHEN** the point lists are shown
- **THEN** Egyesített Kitárolás, UGS-2-SZOREG, MOL Nyrt KTD, Méhkerék "0" pont, the FGSZ `n.a` exit, UGS Chiren, Eustream's Domestic points and the Gas Connect Austria and Trans Austria Gasleitung Baumgarten points other than WAG are absent

#### Scenario: Point counts per TSO
- **WHEN** the real tariff file is loaded
- **THEN** there are 109 single sides and 14 LNG entries, and FGSZ has 14 single sides, Bulgartransgaz 13 and Gastrans 4

#### Scenario: Interruptible-only side is still a single side
- **WHEN** the FGSZ exit Mosonmagyaróvár (HU>AT) has only Interruptible rows
- **THEN** it is offered as an FGSZ single side marked Interruptible

#### Scenario: LNG entries
- **WHEN** the real tariff file is loaded
- **THEN** the LNG entries are Klaipeda (Amber Grid), Agia Triada and Amfitriti (DESFA), Świnoujście (GAZ-SYSTEM), Gate Terminal and Eems Energy Terminal (Gasunie Transport Services), Brunsbüttel and Stade (Gasunie Deutschland), Wilhelmshaven (Open Grid Europe), Omišalj (Plinacro), and Panigaglia, Cavarzere, Ravenna and Piombino (Snam Rete Gas)

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
On the Capacity Fee Calculator:
- a single-side label SHALL use the form "cleaned name flow (EIC)", for example "Csanádpalota RO>HU (21Z000000000236Q)", so that all labels of one TSO are unique, with " - Interruptible" appended for a point that uses Interruptible capacity, for example "Kiskundorozsma 2 HU>RS (21Z000000000505P) - Interruptible";
- a bundled point label SHALL use the form "cleaned name flow (exit TSO + entry TSO)", for example "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)";
- an LNG entry label SHALL use the form "cleaned name (TSO)", for example "Świnoujście (GAZ-SYSTEM)".

Cleaned names SHALL drop the country suffix and the flow from the source name, so that both sides of a border show the same name. On the Route Tariff Calculator each listed point SHALL show its TSO, its cleaned name with flow, its EIC, its direction and its capacity type in separate columns.

#### Scenario: Unique labels on tab 2
- **WHEN** the single-side point dropdown is shown for FGSZ
- **THEN** it has 14 distinct labels, and the points that exist as both entry and exit appear twice with different flows

#### Scenario: Interruptible label
- **WHEN** the single-side point dropdown is shown for Gastrans
- **THEN** the labels of Kiskundorozsma 2 (HU>RS) and Kireevo/Zaychar (RS>BG) end with " - Interruptible" and the other two do not

#### Scenario: Bundle label names both TSOs
- **WHEN** the bundled point dropdown is shown
- **THEN** it contains "Mosonmagyaróvár AT>HU (Gas Connect Austria + FGSZ)" and "Mosonmagyaróvár" is spelled the same for both sides

### Requirement: TSO dropdown
The Capacity Fee Calculator SHALL show a TSO dropdown only for the Single side booking type; it SHALL offer every TSO in scope that has at least one single side, by full name, and its point list SHALL be the single sides of the selected TSO. The Bundled and LNG entry booking types SHALL have no TSO dropdown, since their labels name the TSOs. The Route Tariff Calculator SHALL NOT have a TSO dropdown; the TSOs on a route follow from the border points chosen for it.

#### Scenario: Three TSOs on tab 2
- **WHEN** tab 2 is opened with the booking type Single side on the real tariff file
- **THEN** the TSO dropdown offers all 21 TSOs, and choosing Bulgartransgaz shows its 13 points

#### Scenario: No TSO dropdown for bundles
- **WHEN** the booking type is Bundled
- **THEN** there is no TSO dropdown, only the dropdown of bundled points

#### Scenario: No TSO dropdown on tab 1
- **WHEN** tab 1 is opened
- **THEN** it has no TSO dropdown

### Requirement: Bundled points
The system SHALL offer a bundled point for every border crossing where one TSO's exit and another TSO's entry have the same EIC and the same flow, and both are Firm. A bundled point SHALL consist of exactly those two sides. Crossings where either side is Interruptible SHALL NOT be offered as bundled points; their sides remain available as single sides. At Baumgarten, whose two sides have different EICs, the system SHALL pair Eustream's Baumgarten point (EIC 21Y---A001A023-Y) with Gas Connect Austria's WAG point (EIC 21Z000000000163R): Eustream exit with WAG entry for SK>AT, and WAG exit with Eustream entry for AT>SK. On the real tariff file there SHALL be 43 bundled points.

#### Scenario: Bundle count on the real file
- **WHEN** the real tariff file is loaded
- **THEN** there are 43 bundled points: 41 paired by EIC and the 2 Baumgarten bundles

#### Scenario: Bundle sides
- **WHEN** the bundled point Mosonmagyaróvár AT>HU is chosen
- **THEN** its sides are the Gas Connect Austria exit Mosonmagyaróvár (AT>HU) and the FGSZ entry Mosonmagyaróvár (AT>HU), both with EIC 21Z000000000003C

#### Scenario: Interruptible crossings are not bundled
- **WHEN** the bundled point dropdown is shown on the real tariff file
- **THEN** it offers no bundle for Mosonmagyaróvár HU>AT, Kiskundorozsma 2 HU>RS, Murfeld/Ceršak SI>AT or Kireevo/Zaychar RS>BG

#### Scenario: Baumgarten bundles
- **WHEN** the bundled point dropdown is shown on the real tariff file
- **THEN** it offers "Baumgarten SK>AT (Eustream + Gas Connect Austria)" and "Baumgarten AT>SK (Gas Connect Austria + Eustream)", both using the WAG point on the Austrian side, and no Baumgarten bundle with Trans Austria Gasleitung

### Requirement: Network topology
The system SHALL build the network that tab 1 routes run on from the point catalog. Each point's flow "X>Y" names the country it leaves and the country it enters, using the codes of the tariff data (for example CR for Croatia). A border crossing from X to Y at a point SHALL consist of an exit with flow X>Y of one TSO and an entry with flow X>Y of another TSO at the same point: the same EIC, or for Baumgarten the Eustream point (EIC 21Y---A001A023-Y) with Gas Connect Austria's WAG point (EIC 21Z000000000163R). Each side SHALL be Firm, or Interruptible where it has no Firm row. A map point SHALL be one place where such crossings exist between two countries, offered for both directions where both exist; it is identified by its cleaned name and its two countries. The countries a route can begin or end in SHALL be the countries of these crossings except the pipelines TAP and ICGB, which have their own TSO but no market of their own: on the real tariff file AT, BG, CR, CZ, DE, GR, HU, IT, NL, PL, RO, RS, SI, SK and UA. The points touching TAP or ICGB (Stara Zagora, Komotini, Nea Mesimvria) SHALL NOT be map points. A country MAY have several TSOs; each crossing uses the TSOs that operate its point.

#### Scenario: Map points on the real file
- **WHEN** the real tariff file is loaded
- **THEN** there are 22 map points: Mosonmagyaróvár, VIP Oberkappel, Tarvisio/Arnoldstein, Murfeld/Ceršak, Baumgarten, Kulata/Sidirokastron, Negru Voda 1/Kardam, Ruse/Giurgiu, Kireevo/Zaychar, Drávaszerdahely, Rogatec, VIP Brandov-GASPOOL, Cieszyn, Lanžhot, VIP TTF-THE-H, Csanádpalota, Kiskundorozsma 2, Balassagyarmat, VIP Bereg, Gorizia/Šempeter, Vyrava and Uzhgorod/Velké Kapušany

#### Scenario: Crossing at a point with two TSOs in one country
- **WHEN** gas crosses Tarvisio/Arnoldstein from AT to IT
- **THEN** the crossing is the Trans Austria Gasleitung exit (AT>IT) and the Snam Rete Gas entry (AT>IT), while a crossing at Mosonmagyaróvár into AT uses Gas Connect Austria's entry

#### Scenario: Points without a partner are not map points
- **WHEN** the real tariff file is loaded
- **THEN** Kiskundorozsma (HU>RS, EIC 21Z000000000154S), GCP GAZ-SYSTEM/UA TSO, Beregdaróc, Kipi, Strandzha 1/Malkoclar, Kyustendil/Zidilovo and Mazara del Vallo are not map points, so no route can go from UA to PL
