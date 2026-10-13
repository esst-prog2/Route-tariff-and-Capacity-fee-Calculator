## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Corridor topology
**Reason**: Tab 1 routes are no longer limited to the HU - RS - BG corridor; the trader chooses the border points of a route anywhere in the network.
**Migration**: Routes are built from a beginning country and border points of the network topology (see "Network topology"); the corridor routes stay possible, e.g. BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU.
