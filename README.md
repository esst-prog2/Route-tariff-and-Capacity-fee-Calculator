# Advanced-Programming- Route Tariff and Capacity Fee Calculator

## A brief overview of the natural gas pipeline system
I work in the system usage department of a natural gas trading company. To transport natural gas through pipelines, it is necessary to **book** pipeline capacity sat cross-border interconnection points (**network points**). Each country’s gas network is managed by a Transmission System Operator (**TSO**). In addition to ensuring the security of supply, traders execute profit-oriented transactions. The core strategy is to buy gas where it is cheaper and sell it in markets where prices are higher. When calculating the profit margin for these deals, the capacity booking costs along the transport **route** are taken into account.
**Capacity booking** is conducted on the respective TSO's system for specific **product instruments**, which can be **yearly, quarterly, monthly, daily**, or within-day products. At my current company, we hold active network usage contracts in 14 different countries.

**The objective of the project is to develop an application or interface that quickly, clearly, and simply provides traders with the relevant costs. This will not only support their daily work, but also significantly reduce our department's workload.**

## 1. The demo
The MVP works with FGSZ (Hungary) Firm capacity at 12 cross-border points (7 entries, 5 exits); every calculation below is HUF-based and uses the synthetic sample in `data/sample/`. Run it with `python -m streamlit run app.py`.

**Route Tariff Calculator.** I open the app in the browser and stay on the "Route Tariff Calculator" tab. TSO: FGSZ. Entry point "Mosonmagyaróvár (21Z000000000003C)", exit point "Kiskundorozsma (21Z000000000154S)", booking period 2026-10-01 to 2027-03-31 (both dates inclusive). I type today's FX rate, for example 400 HUF per EUR. The screen shows the cheapest combination of quarterly, monthly and daily products for entry + exit together: Q4 as one quarterly product, then January, February and March as monthly products, with a "Tariff used" column showing which tariff row each price came from. With the sample data the route costs 4134.1287 HUF per kWh/h, which is 946.4580 HUF/MWh or 2.3661 EUR/MWh at 400 HUF/EUR, against 4.0796 EUR/MWh if every day were booked as a daily product (a saving of 2993.8050 HUF per kWh/h). Without an FX rate the HUF figures are still shown and the EUR/MWh column is left out.

**Capacity Fee Calculator.** I switch to the "Capacity Fee Calculator" tab. TSO: FGSZ, network point "Kiskundorozsma 2 RS>HU (21Z000000000505P)", product instrument "Quarter", 2026 Q4, requested capacity 50,000 kWh/d. The app converts it to 2083.33 kWh/h and calculates the total: 1,565,115 HUF, with the monthly invoice below it: October 527,376 HUF, November 510,363 HUF, December 527,376 HUF (split by calendar days, adding up exactly to the total).

## 2. The shape
* in: a CSV/Excel export of network capacity tariffs, plus a user query specifying origin point, destination point, booking period, TSO, product instrument 
* out: an optimized unit tariff breakdown, the total calculated cost for the requested volume
* on screen: Two tabs, on the first one a calculator panel with dropdowns for network points, dates and a results dashboard showing the optimal (cheapest) product combination in EUR/MWh. On the other tab an input field for the capacity volume, network point, TSO, product instrument and a results dashboard showing the cost of the capacity, and the calculated invoice for a month.

## 3. The size
### What the first useful version does:
* Parse and load the standard tariff Excel/CSV file into a queryable structure.
* Find the optimal combination of yearly/monthly/daily tariff for a specific time period, for it to be the cheapest way.
* Calculate the total payable fee based on a user-defined capacity volume and break it down into monthly costs.
* Uses the data of one TSO, FGSZ, in the MVP (the other TSOs are deferred)

### What it explicitly does not do this term:
* Live API integration with ENTSOG, Regional Booking Platform or TSO websites for automatic data fetching (files will be uploaded manually).
* Multi-currency conversion via real-time external exchange APIs (it calculates in the source currency).
* Multi-node route optimization (it will calculate costs for one specified network point at a time, not a full cross-border route, the route's sum of tariffs would be presented only).
* Calculating the necessary financial security that needs to be held at the TSO by the System User for a given capacity booking request.
* Doesn't calculate with within-day capacity products.

## 4. How we would know it works
* Given a specific capacity volume for a quarterly period, the sum of the generated monthly cost breakdown equals the exact calculated total cost.
* Given a not acceptable route, instead of crashing, it displays a message saying the route is not possible.
* Given a booking request that crosses the October 1st gas year boundary, it correctly splits the period, applying the old tariff up to September 30 and the new tariff from October 1 onwards.

## 5. What could stop this
* The logic for mixing different countries and TSOs capacity fee calculators might have too many irregular methods to put all together in the same way.
* The structure of the source Excel file might be inconsistent (e.g., unexpected empty cells,) which could break the parser.
* Handling leap years and exact timezone boundaries in the booking period to parsing might prove unexpectedly complex.

The database is not public so a sythetic sample with the same columns will be used, with the real export hidden.

## Running the MVP
```
pip install -r requirements.txt
python -m streamlit run app.py     # uses the synthetic sample in data/sample/
python -m pytest                   # unit, app and acceptance tests
```
To use the real export, keep it in `data/private/` (git-ignored, never committed) and point the app at it with the `FGSZ_TARIFF_FILE` environment variable, or upload it in the sidebar for one session. The parser reports missing columns and unusable rows in plain language instead of crashing.
