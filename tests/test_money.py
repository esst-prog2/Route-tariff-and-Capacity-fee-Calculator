from fractions import Fraction

import pytest

from core import money


def test_float_prices_become_exact_decimals():
    assert money.to_fraction(751.255428) == Fraction(751255428, 1_000_000)
    assert money.to_fraction("50000") == 50000
    assert money.to_fraction(7) == 7


@pytest.mark.parametrize("bad", ["abc", "", "nan", float("nan"), float("inf")])
def test_non_numeric_values_are_rejected(bad):
    with pytest.raises(ValueError):
        money.to_fraction(bad)


def test_round_whole_halves_away_from_zero():
    assert money.round_whole(Fraction(5, 2)) == 3
    assert money.round_whole(Fraction(-5, 2)) == -3
    assert money.round_whole(Fraction(249, 100)) == 2


def test_demo_total_and_breakdown():
    total = money.round_whole(money.to_fraction(50000) / 24 * money.to_fraction(751.255428))
    assert total == 1_565_115
    assert money.split_by_weights(total, [31, 30, 31]) == [527_376, 510_363, 527_376]


def test_split_always_sums_to_the_total():
    for total in [0, 1, 2, 999, 1_565_115, 7_654_321]:
        for weights in ([31, 30, 31], [30, 31, 30, 31, 31], [365], [31] * 12, [1, 1, 1]):
            shares = money.split_by_weights(total, weights)
            assert sum(shares) == total
            assert all(s >= 0 for s in shares)


def test_split_tie_goes_to_earlier_share():
    assert money.split_by_weights(2, [1, 1, 1]) == [1, 1, 0]


def test_format_decimal_rounds_half_up_for_display():
    assert money.format_decimal(Fraction(53210, 10000), 4) == "5.3210"
    assert money.format_decimal(Fraction(1, 3), 4) == "0.3333"
    assert money.format_decimal(Fraction(5, 10000), 3) == "0.001"
    assert money.format_whole(1565115) == "1,565,115"
