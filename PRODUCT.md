# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML/CSS for the promo page: `docs/index.html` with its stylesheet, fonts and images beside it, served by GitHub Pages from the `/docs` folder of `main`, no build step. The app itself is a Python Streamlit app (`app.py`, `core/`), hosted on Streamlit Community Cloud.

## Users

Gas traders who book pipeline capacity at cross-border interconnection points in Central and Eastern Europe. Their job: before a deal, know what moving gas along a route will cost, what each operator will invoice, and what financial guarantee the operator will ask for. Today they ask the system usage team, who work it out by hand from each operator's tariff sheet.

This term the promo page is read by people who do not know gas trading: a classmate, the course teacher, and a stranger.

## Product Purpose

Route Tariff and Capacity Fee Calculator answers three questions from the real tariff data, in three tabs:
- Route Tariff Calculator: the trader picks a route's border points on a map; the app finds the cheapest mix of yearly, quarterly, monthly and daily products for each operator on the route and gives the route's cost in EUR/MWh.
- Capacity Fee Calculator: the capacity fee of a booking at one point (bundled, single side or LNG entry), in each operator's own currency, split into the monthly invoices the operator will send.
- Bank Guarantee Calculator: the financial guarantee Eustream asks for a booking (only Eustream's rule so far).

Success: a trader gets the answer alone, in seconds, without asking the department.

## Positioning

Free, and covers 21 operators at once, each with its own currency, unit, products and invoicing rule; there is no free calculator across operators (TSOs publish only their own tariff sheets; the closest tool found is a commercial route calculator inside a paid data platform).

## Operating Context

- Live app: https://route-tariff-and-capacity-fee-calculator.streamlit.app (sleeps when unused; waking takes about a minute).
- Code: https://github.com/esst-prog2/Route-tariff-and-Capacity-fee-Calculator
- Built for the Advanced Programming course at ELTE, 2026; presented on demo days 1 and 8 December 2026.

## Capabilities and Constraints

- Tariffs come from one file (`data/real/tariffs_real.xlsx`, last updated 29 October 2026), public on each operator's website and collected by hand; not fetched live.
- Routes run across 22 border points between 15 countries; the trader picks the points, the app does not search for a path.
- Exchange rates are typed in; no within-day products; it does not book capacity.
- Terminology: TSO (transmission system operator), network point, product (year, quarter, month, day), capacity in kWh/h or kWh/d, EUR/MWh.

## Brand Commitments

None: no logo, no brand colours. No company name, no personal names (the author's included), no colleagues, no faces on the page.

## Evidence on Hand

- The three worked examples, all asserted in `tests/`: route BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU, 1 Oct 2026 to 31 Mar 2027, 400 HUF per EUR: 3.6957 EUR/MWh, quarters save 0.2956; Mosonmagyaróvár AT>HU Q4 2026 at 50,000 kWh/d: 2,605.83 EUR + 782,558 HUF; Eustream Balassagyarmat SK>HU Q4 2026, 100,000 kWh/h, booked, CEGHIX 30: capacity fee 361,344.00 EUR, guarantee 280,104.80 EUR.
- Over 400 automated tests (425 on 13 November 2026).
- Screenshots: captured from a real local run of the app for these examples. No testimonials, users, customers or usage numbers exist; none may be invented.
- Page copy: `designs/promo-page-content.md` (approved).

## Product Principles

1. Every number has a source: a calculated figure on the page is one a test asserts.
2. Explain before pitching: one plain line on the problem for readers who don't know gas trading.
3. Honest limits: say what it does not do (no booking, no live tariffs, guarantee only for Eustream).
4. Nothing personal leaves the machine.

## Accessibility & Inclusion

English only. The page must work on a phone and on the shared projector computer on demo day.
