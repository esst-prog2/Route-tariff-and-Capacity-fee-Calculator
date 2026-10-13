## 1. Optimiser: longest product allowed

- [ ] 1.1 Add an optional "longest product allowed" parameter to `optimize` (default yearly = today's behaviour) that skips gas years, quarters and months above it; verify with new `tests/test_optimizer.py` cases (quarterly-limited, monthly-limited, daily-only) and that all existing optimiser tests pass unchanged

## 2. Route: per-point figures and the comparison

- [ ] 2.1 Compute each point's cost from its TSO's chosen segments and its own prices, and its per-MWh and EUR/MWh figures (FGSZ via the FX rate); verify in `tests/test_route.py` that the points' costs add up exactly to the leg total and their EUR/MWh to the route total, and the Gastrans split scenario (0.8494 / 0.9684 on the real tariffs)
- [ ] 2.2 Add the next-shorter comparison per leg (longest type in the cheapest plan, comparison plan, EUR/MWh) and for the route (sum, saving, label: "Without ... products" or "Next shorter products" with the per-TSO note; none when every TSO is daily only); verify with route tests for same-level, mixed-level, monthly-vs-daily and daily-only cases
- [ ] 2.3 Verify the existing route and acceptance tests (including the README sample figures and the all-daily totals) still pass unchanged

## 3. Product labels

- [ ] 3.1 Add a function that turns a plan and the period into the Products text (GY, Q, month, month runs, daily stretches, "(+N days)"); verify with unit tests for the four Product labels scenarios plus a single daily day and "(+1 day)"

## 4. Tab 1 layout

- [ ] 4.1 Rebuild `route_tab` in `app.py`: one point table with Products and EUR/MWh, the over-booking note, the route total (cheapest, comparison, saving, label note), the FX prompt when the rate is missing, and a closed "Details" expander with tariff used per point and product; remove the per-TSO product tables and the summary per TSO; verify by running the app headlessly in `tests/test_app.py`
- [ ] 4.2 Rewrite the tab 1 app tests for the new layout (columns, EUR/MWh cells adding up to the route total, no per-TSO tables, empty FGSZ cell and prompt without a rate, saving = comparison - cheapest, Details present) and verify `python -m pytest` passes

## 5. Docs and wrap-up

- [ ] 5.1 Rewrite the tab 1 part of README section 1 for the new layout and verify every figure it quotes against the app
- [ ] 5.2 Record any implementation decisions taken while applying the change in `PLANNING_LOG.md`
- [ ] 5.3 Run the app on the real tariffs and check BG to HU 2026-10-01 to 2027-03-31 (1.4431 / 0.8494 / 0.9684 / 0.4348; 3.6957, 3.9913, 0.2956 at 400 HUF/EUR) and one over-booked and one mixed-product period by eye (user)
