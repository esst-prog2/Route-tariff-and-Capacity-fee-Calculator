"""Spike (throwaway): how much does exact-cover pricing lose against allowing
over-booking?

Run from the project root:  python <this file>  [optional tariff file]

To reproduce the logged numbers (median 0.0 %, worst 135.8 %), run it against
the code as it was before over-booking was allowed, i.e. commit 2d18ce7:
    git worktree add ../spike-base 2d18ce7
    cd ../spike-base
    python <path to this file>
On later commits the optimiser itself over-books, so every overpay is 0.0 %.

For every entry x exit pair (7 x 5 = 35) and every period below, compare
  exact = core.optimizer.optimize(...).total   (what the app shows)
  over  = cheapest plan made of quarters / months / days that covers every
          booked day but may also cover days outside the period.
Products are calendar-aligned and nest (day < month < quarter), so the
cheapest over-cover is exact by working bottom-up per quarter:
  month cost   = min(monthly price, sum of the day prices of booked days)
  quarter cost = min(quarterly price, sum of its touched months' costs)
Prices come from the app's own RouteOracle (row valid on product's first day),
so both sides use the same tariff lookup. Yearly is left out, as in the app.
"""

from __future__ import annotations

import statistics
import sys
from datetime import date
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from core import periods  # noqa: E402
from core.optimizer import optimize  # noqa: E402
from core.points import entries, exits  # noqa: E402
from core.route import RouteOracle  # noqa: E402
from core.tariffs import DEFAULT_SAMPLE_PATH, load_tariffs  # noqa: E402

D = date
PERIODS = [
    # the two cases from the review
    (D(2026, 10, 2), D(2026, 12, 30), "review: Q4 minus first and last day"),
    (D(2026, 11, 2), D(2026, 11, 28), "review: November 2-28"),
    # a month minus a few edge days
    (D(2026, 12, 2), D(2026, 12, 31), "December from the 2nd"),
    (D(2027, 1, 1), D(2027, 1, 30), "January to the 30th"),
    (D(2027, 2, 3), D(2027, 2, 26), "February 3-26"),
    (D(2027, 3, 5), D(2027, 3, 31), "March from the 5th"),
    # exact months and quarters
    (D(2026, 11, 1), D(2026, 11, 30), "full November"),
    (D(2027, 1, 1), D(2027, 1, 31), "full January"),
    (D(2026, 10, 1), D(2026, 12, 31), "full Q4 2026"),
    (D(2027, 1, 1), D(2027, 3, 31), "full Q1 2027"),
    # a quarter minus a few edge days
    (D(2027, 1, 4), D(2027, 3, 31), "Q1 from the first Monday"),
    (D(2027, 4, 1), D(2027, 6, 27), "Q2 to the 27th of June"),
    (D(2027, 7, 2), D(2027, 9, 29), "Q3 minus 1 + 1 day"),
    # short bookings
    (D(2026, 10, 5), D(2026, 10, 11), "one week in October"),
    (D(2027, 2, 15), D(2027, 2, 21), "one week in February"),
    (D(2026, 12, 24), D(2026, 12, 24), "single day"),
    (D(2026, 12, 1), D(2026, 12, 15), "first half of December"),
    (D(2027, 5, 10), D(2027, 5, 23), "two weeks in May"),
    # balance of month
    (D(2026, 10, 15), D(2026, 10, 31), "balance of October"),
    (D(2027, 1, 18), D(2027, 1, 31), "balance of January"),
    (D(2027, 1, 25), D(2027, 2, 7), "two weeks across a month end"),
    # multi-month
    (D(2026, 10, 1), D(2027, 3, 31), "README demo: winter half-year"),
    (D(2027, 4, 1), D(2027, 9, 30), "summer half-year"),
    (D(2026, 10, 20), D(2027, 2, 10), "ragged winter block"),
    (D(2026, 11, 15), D(2027, 1, 15), "mid-Nov to mid-Jan"),
    (D(2027, 3, 10), D(2027, 5, 20), "ragged spring block"),
    (D(2025, 10, 1), D(2025, 12, 20), "last year's Q4 to Dec 20"),
    # across the 1 October gas-year boundary
    (D(2026, 9, 15), D(2026, 10, 15), "Sep 15 - Oct 15 across gas year"),
    (D(2026, 8, 1), D(2026, 11, 30), "Aug - Nov across gas year"),
    (D(2026, 9, 20), D(2026, 10, 31), "Sep 20 - Oct 31 across gas year"),
]


def over_cover_total(start: date, end: date, oracle: RouteOracle) -> Fraction:
    months_by_quarter: dict[tuple[int, int], Fraction] = {}
    for s in periods.month_slices(start, end):
        days = sum((oracle.day_price(d) for d in periods.iter_days(s.first, s.last)), Fraction(0))
        month_cost = min(oracle.month_price(s.year, s.month), days)
        key = (s.year, periods.quarter_of_month(s.month))
        months_by_quarter[key] = months_by_quarter.get(key, Fraction(0)) + month_cost
    return sum(
        (min(oracle.quarter_price(y, q), cost) for (y, q), cost in months_by_quarter.items()),
        Fraction(0),
    )


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE_PATH
    table = load_tariffs(path).table
    rows = []
    for entry in entries():
        for exit_ in exits():
            oracle = RouteOracle(table, entry, exit_)
            for start, end, label in PERIODS:
                exact = optimize(start, end, oracle).total
                over = over_cover_total(start, end, oracle)
                assert over <= exact, (entry, exit_, start, end)
                rows.append((float((exact - over) / over * 100), float(exact), float(over), entry, exit_, start, end, label))

    pairs = {(r[3], r[4]) for r in rows}
    overpays = [r[0] for r in rows]
    print(f"tariff file: {path.name}")
    print(f"pairs: {len(pairs)}, periods: {len(PERIODS)}, cases: {len(rows)}")
    print(f"median overpay: {statistics.median(overpays):.1f}%")
    worst = max(rows, key=lambda r: r[0])
    print(f"worst overpay:  {worst[0]:.1f}%  ({worst[3].cleaned_name} -> {worst[4].cleaned_name}, "
          f"{worst[5]}..{worst[6]} '{worst[7]}': {worst[1]:.1f} vs {worst[2]:.1f})")
    valid = [r[0] for r in rows if r[3].eic != r[4].eic]
    print(f"excluding the 4 same-EIC pairs the app rejects ({len(valid)} cases): "
          f"median {statistics.median(valid):.1f}%, worst {max(valid):.1f}%")
    print(f"cases with any overpay: {sum(o > 0 for o in overpays)} of {len(rows)}")

    print("\nper period (median / worst over pairs):")
    for start, end, label in PERIODS:
        ps = [r[0] for r in rows if r[5] == start and r[6] == end]
        print(f"  {start}..{end}  {statistics.median(ps):6.1f}% {max(ps):6.1f}%  {label}")

    print("\nreview spot-checks (Mosonmagyarovar -> Kiskundorozsma):")
    for r in rows:
        if r[3].name == "Mosonmagyaróvár" and r[4].name == "Kiskundorozsma" and r[7].startswith("review"):
            print(f"  {r[5]}..{r[6]}: exact {r[1]:.1f}, over-cover {r[2]:.1f}, overpay {r[0]:.1f}%")


if __name__ == "__main__":
    main()
