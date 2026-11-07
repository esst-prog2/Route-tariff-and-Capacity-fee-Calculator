## 1. Keep the long walk-throughs

- [x] 1.1 Move the two walk-throughs now in section 1 (the "Route Tariff Calculator." and "Capacity Fee Calculator." paragraphs, with the introductory paragraph about the 21 TSOs and the map) unchanged to a new section "## Walk-through of tabs 1 and 2" after "## Running the MVP"; verify with `git diff` that the moved text matches the old text word for word

## 2. Rewrite section 1

- [x] 2.1 Replace the body of "## 1. The demo" with three to six present-tense sentences: the hosted app's address and `data/real/tariffs_real.xlsx`, then one example per tab (route BG > Kireevo/Zaychar > RS > Kiskundorozsma 2 > HU, 2026-10-01 to 2027-03-31, 400 HUF per EUR, 3.6957 EUR/MWh, 0.2956 saved by the quarters; bundle Mosonmagyaróvár AT>HU, 2026 Q4, 50,000 kWh/d, 2,605.83 EUR + 782,558 HUF = 4,584.48 EUR at 395.5; Eustream Balassagyarmat SK>HU, 2026 Q4, 100,000 kWh/h, booked, CEGHIX 30, capacity fee 361,344.00 EUR, guarantee 280,104.80 EUR); verify the sentence count is between three and six
- [x] 2.2 Check each figure in the new section 1 in the running app (`python -m streamlit run app.py`) by following the three examples as written, and run `python -m pytest` to confirm the tests that cover these figures still pass

## 3. Record and publish

- [x] 3.1 Add the decisions of this change to `PLANNING_LOG.md`, commit on `main`, push to `origin`, and verify `git status -sb` shows `main...origin/main` with nothing ahead
