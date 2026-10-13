# Advanced-Programming- Route Tariff and Capacity Fee Calculator

## A brief overview of the natural gas pipeline system
I work in the system usage department of a natural gas trading company. To transport natural gas through pipelines, it is necessary to **book** pipeline capacity sat cross-border interconnection points (**network points**). Each country’s gas network is managed by a Transmission System Operator (**TSO**). In addition to ensuring the security of supply, traders execute profit-oriented transactions. The core strategy is to buy gas where it is cheaper and sell it in markets where prices are higher. When calculating the profit margin for these deals, the capacity booking costs along the transport **route** are taken into account.
**Capacity booking** is conducted on the respective TSO's system for specific **product instruments**, which can be **yearly, quarterly, monthly, daily**, or within-day products. At my current company, we hold active network usage contracts in 14 different countries.

**The objective of the project is to develop an application or interface that quickly, clearly, and simply provides traders with the relevant costs. This will not only support their daily work, but also significantly reduce our department's workload.**

## 1. The demo
The app works with three TSOs along the Hungary - Serbia - Bulgaria corridor: FGSZ (Hungary, HUF per kWh/h), Gastrans (Serbia, EUR per kWh/h) and Bulgartransgaz (Bulgaria, EUR per kWh/d, from 2026-01-01 when its tariffs switched from BGN to EUR). It uses Firm capacity, and Interruptible capacity only at the three points that have no Firm tariff (the north-to-south direction at Kiskundorozsma 2 and Kireevo/Zaychar). The route walk-through below uses the real tariffs in `data/real/`, the capacity fee walk-through the synthetic sample in `data/sample/`. Open it at https://route-tariff-and-capacity-fee-calculator.streamlit.app (or run it locally, see [Running the MVP](#running-the-mvp)).

**Route Tariff Calculator.** I open the app in the browser and stay on the "Route Tariff Calculator" tab. Route beginning: BG, route ending: HU, booking period 2026-10-01 to 2027-03-31 (both dates inclusive). Because the route touches Hungary I type today's FX rate, for example 400 HUF per EUR. A route runs hub to hub, so the app shows one table of the four network points the gas crosses: Bulgartransgaz exit Kireevo/Zaychar (BG>RS), Gastrans entry Kireevo/Zaychar (BG>RS), Gastrans exit Kiskundorozsma 2 (RS>HU) and FGSZ entry Kiskundorozsma 2 (RS>HU), each with its EIC, direction, capacity type, the products it books and its cost in EUR/MWh. Each TSO is optimised on its own, in its own currency and unit (the two Gastrans points share one product choice); here every point books "Q4 2026, Q1 2027". On the real tariffs the points cost 1.4431, 0.8494, 0.9684 and 0.4348 EUR/MWh, which add up to the route total: 3.6957 EUR/MWh. Below it the app compares each TSO with the next shorter products it could have booked, here "Without quarterly products": 3.9913 EUR/MWh, so the quarters save 0.2956 EUR/MWh. For a whole gas year (2026-10-01 to 2027-09-30) every point books "GY 2026/27", the route costs 2.7400 EUR/MWh, and the comparison is "Without yearly products" (3.3411, a saving of 0.6010). Without an FX rate the FGSZ cell stays empty and the route total waits for the rate; a BG to RS route needs no rate at all. If the period misses a few days at the edge of a month or quarter, the optimiser may **over-book**: it buys the whole month or quarter when that is cheaper than covering only the booked days. For example, for 2026-10-02 to 2026-12-30 every point reads "Q4 2026 (+2 days)" and a note explains the over-booking; the route costs 3.6415 EUR/MWh, because per-MWh figures still divide by the booked days only. A closed "Details" section lists every point's products with their dates and the tariff row each price came from. Choosing HU to BG lists the three Interruptible points with a warning that the TSO can interrupt that capacity.

**Capacity Fee Calculator.** I switch to the "Capacity Fee Calculator" tab. TSO: FGSZ, network point "Kiskundorozsma 2 RS>HU (21Z000000000505P)", product instrument "Quarter", 2026 Q4, requested capacity 50,000 kWh/d. The app converts it to 2083.33 kWh/h and calculates the total: 1,565,115 HUF, with the monthly invoice below it: October 527,376 HUF, November 510,363 HUF, December 527,376 HUF (split by calendar days, adding up exactly to the total). Switching the TSO to Bulgartransgaz and the point to "Kireevo/Zaychar BG>RS (58Z-000000007-KZ)", the same 50,000 kWh/d is used as it is, because Bulgartransgaz prices per kWh/d: the total is 12,110.87 EUR, invoiced as 4,080.84, 3,949.20 and 4,080.83 EUR (EUR amounts are rounded to cents).

## 2. The shape
* in: a CSV/Excel export of network capacity tariffs, plus a user query specifying the route's beginning and ending country (or, on tab 2, a TSO and network point), booking period, product instrument 
* out: an optimized unit tariff breakdown, the total calculated cost for the requested volume
* on screen: Two tabs, on the first one a calculator panel with "Route beginning" and "Route ending" dropdowns (HU, RS, BG), dates and a results dashboard listing every network point on the route and the optimal (cheapest) product combination per TSO, with the route total in EUR/MWh. On the other tab an input field for the capacity volume, TSO, network point, product instrument and a results dashboard showing the cost of the capacity in the point's own currency, and the calculated invoice for a month.

## 3. The size
### What the first useful version does:
* Parse and load the standard tariff Excel/CSV file into a queryable structure.
* Find the cheapest combination of yearly/quarterly/monthly/daily products that covers a specific time period, over-booking whole months, quarters or gas years outside the period when that is cheaper.
* Calculate the total payable fee based on a user-defined capacity volume and break it down into monthly costs.
* Uses the data of three TSOs, FGSZ, Gastrans and Bulgartransgaz, and prices hub-to-hub routes along the HU - RS - BG corridor (the other TSOs are deferred)

### What it explicitly does not do this term:
* Live API integration with ENTSOG, Regional Booking Platform or TSO websites for automatic data fetching (files will be uploaded manually).
* Multi-currency conversion via real-time external exchange APIs (it calculates in the source currency; the route's EUR/MWh uses an FX rate the trader types in).
* Routes beyond the HU - RS - BG corridor, or choosing between alternative paths (each route has exactly one path, and each TSO on it is optimised separately).
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

The project now uses the real tariff data, committed as `data/real/tariffs_real.xlsx`. The tariffs are public on the TSOs' websites, and my employer allowed me to use them. The file is the work export without its author and comment columns. The synthetic sample in `data/sample/` is kept, because the demo figures above and the earlier tests were built on it.

## Running the MVP
The app is hosted on Streamlit Community Cloud: **https://route-tariff-and-capacity-fee-calculator.streamlit.app**. It opens the synthetic sample by default; the real tariffs can be uploaded in the sidebar. If nobody has opened it for a while it shows a "gone to sleep" page; click the button to wake it (about a minute).

To run it locally instead:
```
pip install -r requirements.txt
python -m streamlit run app.py     # uses the synthetic sample in data/sample/
python -m pytest                   # unit, app and acceptance tests
```
To use the real tariffs, point the app at `data/real/tariffs_real.xlsx` with the `FGSZ_TARIFF_FILE` environment variable (PowerShell: `$env:FGSZ_TARIFF_FILE = "data/real/tariffs_real.xlsx"`, then `python -m streamlit run app.py`), or upload it in the sidebar for one session. The raw work export, which still has colleagues' names in it, stays in `data/private/` (git-ignored, never committed). The parser reports missing columns and unusable rows in plain language instead of crashing.
