"""Exact money arithmetic. Amounts are `fractions.Fraction` so that
capacity / 24 x price carries no binary floating-point error; rounding
happens only when a value is finally shown or split."""

from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from typing import Sequence


def to_fraction(value) -> Fraction:
    """Exact Fraction from an int, float, Decimal or numeric string.

    Floats go through their shortest repr, so 751.255428 becomes exactly
    751255428/1000000 instead of its binary expansion."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, (str, Decimal)):
        return Fraction(str(value).strip())  # ValueError for non-numeric text
    return Fraction(str(float(value)))  # floats, numpy scalars; ValueError for nan/inf


_PLAIN_NUMBER = re.compile(r"[+-]?\d+(\.\d+)?")
_THOUSANDS_COMMAS = re.compile(r"\d{1,3}(,\d{3})+(\.\d+)?")


def parse_number(text) -> Fraction:
    """Parse a number a person typed. Spaces are ignored, "50,000" is fifty
    thousand and "395,5" is 395.5. Raises ValueError for anything else."""
    cleaned = re.sub(r"[\s_]", "", str(text))
    if _THOUSANDS_COMMAS.fullmatch(cleaned):
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    if not _PLAIN_NUMBER.fullmatch(cleaned):
        raise ValueError(f"not a number: {text!r}")
    return Fraction(cleaned)


def round_whole(amount: Fraction) -> int:
    """Round to a whole number, halves away from zero."""
    sign = -1 if amount < 0 else 1
    return sign * math.floor(abs(amount) + Fraction(1, 2))


def split_by_weights(total: int, weights: Sequence[int]) -> list[int]:
    """Split a whole amount in proportion to `weights`.

    Each share is rounded down, then the forints left over go one each to
    the shares with the largest fractional parts (earlier share wins a tie),
    so the parts always add up to exactly `total`."""
    weight_sum = sum(weights)
    exact = [Fraction(total * w, weight_sum) for w in weights]
    shares = [math.floor(x) for x in exact]
    leftover = total - sum(shares)
    order = sorted(range(len(weights)), key=lambda i: (-(exact[i] - shares[i]), i))
    for i in order[:leftover]:
        shares[i] += 1
    return shares


def format_decimal(amount: Fraction, places: int) -> str:
    """Fixed-decimal text, rounded half up (display only)."""
    with localcontext() as ctx:
        ctx.prec = 60
        value = Decimal(amount.numerator) / Decimal(amount.denominator)
        return str(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def format_whole(amount: int) -> str:
    return f"{amount:,}"
