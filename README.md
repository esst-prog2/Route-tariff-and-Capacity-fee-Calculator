# Advanced-Programming- Route Tariff and Capacity Fee Calculator

## A brief overview of the natural gas pipeline system
I work in the system usage department of a natural gas trading company. To transport natural gas through pipelines, it is necessary to **book** pipeline capacity sat cross-border interconnection points (**network points**). Each country’s gas network is managed by a Transmission System Operator (**TSO**). In addition to ensuring the security of supply, traders execute profit-oriented transactions. The core strategy is to buy gas where it is cheaper and sell it in markets where prices are higher. When calculating the profit margin for these deals, the capacity booking costs along the transport **route** are taken into account.
**Capacity booking** is conducted on the respective TSO's system for specific **product instruments**, which can be **yearly, quarterly, monthly, daily**, or within-day products. At my current company, we hold active network usage contracts in 14 different countries.

**The objective of the project is to develop an application or interface that quickly, clearly, and simply provides traders with the relevant costs. This will not only support their daily work, but also significantly reduce our department's workload.**

## 1. The demo
I open the app in the browser, I am on the "Route Tariff Calculator" tab and select the origin network point "Kiskundorozsma 2", destination network point "UGS Chiren". I input a date range for capacity booking: 2026.12.05 - 2027.01.15. The screen instantly displays the calculated optimal (cheapest) tariff in EUR/MWh, comparing the cost of buying strictly daily products versus a combination of monthly and daily products. 
I switch to the "Capacity Fee Calculator" tab and enter a requested capacity of 50,000 kWh/d for the network point "Kiskundorozsma 2", select the Transmission System Operator "FGSZ", and the product instrument: 2026 Q4. The app calculates the exact total cost in the given currency: XXX HUF, and below it, a breakdown showing the calculated monthly invoice XXX HUF.

## 2. The shape
* in: a CSV/Excel export of network capacity tariffs, plus a user query specifying origin point, destination point, booking period, TSO, product instrument 
* out: an optimized unit tariff breakdown, the total calculated cost for the requested volume
* on screen: Two tabs, on the first one a calculator panel with dropdowns for network points, dates and a results dashboard showing the optimal (cheapest) product combination in EUR/MWh. On the other tab an input field for the capacity volume, network point, TSO, product instrument and a results dashboard showing the cost of the capacity, and the calculated invoice for a month.

## 3. The size
### What the first useful version does:
* Parse and load the standard tariff Excel/CSV file into a queryable structure.
* Find the optimal combination of yearly/monthly/daily tariff for a specific time period, for it to be the cheapest way.
* Calculate the total payable fee based on a user-defined capacity volume and break it down into monthly costs.
* Uses the data of 3 TSOs

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
