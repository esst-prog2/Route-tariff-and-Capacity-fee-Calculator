"""Bank Guarantee Calculator: the financial guarantee a TSO requires for one
capacity booking, at a capacity auction or for booked capacity.

Each TSO has its own rule in `GUARANTEE_RULES`; the public entry point is
`calculate_guarantee`, which returns a `GuaranteeResult` or a `FeeError`
carrying a message for the user. Amounts are exact until they are rounded
to cents, as on tab 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Callable

from .fee import GAS_YEAR, QUARTER, FeeError, FeeResult, calculate_fee
from .money import EUR, parse_number, round_minor
from .points import EUSTREAM, Point
from .tariffs import TariffTable

AUCTION = "Capacity auction"  # the guarantee covers the capacity fee only
BOOKED = "Booked capacity"  # it also covers the GfON
STAGES = (AUCTION, BOOKED)

CEGHIX_MESSAGE = "CEGHIX must be a positive number."
CEGHIX_NOTE = "Enter the CEGHIX valid on the day before the booking."

# Products longer than two months, whose guarantee is two months' payment instead of the total.
TWO_MONTH_INSTRUMENTS = (GAS_YEAR, QUARTER)


@dataclass(frozen=True)
class GuaranteeResult:
    """Amounts in cents of `currency`; the GfON fields are None at a capacity auction."""

    fee: FeeResult
    capacity_fee: int
    capacity_fee_guarantee: int
    gfon_fee: int | None = None
    gfon_fee_guarantee: int | None = None

    @property
    def currency(self) -> str:
        return self.fee.currency

    @property
    def total_guarantee(self) -> int:
        return self.capacity_fee_guarantee + (self.gfon_fee_guarantee or 0)


def parse_ceghix(text) -> Fraction | FeeError:
    """A typed CEGHIX in EUR/MWh: a positive number, else the CEGHIX message."""
    try:
        ceghix = parse_number(text)
    except ValueError:
        return FeeError(CEGHIX_MESSAGE)
    return ceghix if ceghix > 0 else FeeError(CEGHIX_MESSAGE)


def gfon_rate(ceghix: Fraction) -> Fraction:
    """Eustream's neutrality fee (GfON) in EUR/MWh: (CEGHIX + 1) x 0.85 / 100, not rounded."""
    return (ceghix + 1) * Fraction(85, 100) / 100


def _two_largest(amounts) -> Fraction | int:
    return sum(sorted(amounts, reverse=True)[:2])


def eustream_guarantee(result: FeeResult, ceghix: Fraction | None) -> GuaranteeResult:
    """Operational Order 7.6.2: for a gas year or quarter two months' payment (the two most
    expensive months), for a month or day the whole payment; separately for the capacity fee
    and, once the capacity is booked (`ceghix` given), for the GfON."""
    two_months = result.instrument in TWO_MONTH_INSTRUMENTS
    capacity_guarantee = _two_largest(line.amount for line in result.invoice) if two_months else result.total
    if ceghix is None:
        return GuaranteeResult(result, result.total, capacity_guarantee)

    # Full use of the booked capacity, 24 hours every gas day: kWh/d x days / 1000 = MWh per month.
    rate = gfon_rate(ceghix)
    monthly = [result.capacity_kwh_d * line.days / 1000 * rate for line in result.invoice]
    gfon = round_minor(sum(monthly, Fraction(0)), result.currency)
    gfon_guarantee = round_minor(_two_largest(monthly), result.currency) if two_months else gfon
    return GuaranteeResult(result, result.total, capacity_guarantee, gfon, gfon_guarantee)


GUARANTEE_RULES: dict[str, Callable[[FeeResult, Fraction | None], GuaranteeResult]] = {
    EUSTREAM: eustream_guarantee,
}


def calculate_guarantee(
    table: TariffTable,
    point: Point,
    instrument: str,
    start: date,
    end: date,
    capacity_text,
    capacity_unit: str,
    stage: str,
    ceghix_text=None,
) -> GuaranteeResult | FeeError:
    """The guarantee for one booking at `point` (a TSO in `GUARANTEE_RULES`); `ceghix_text`
    is read only for booked capacity."""
    if stage not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}")
    rule = GUARANTEE_RULES[point.tso]
    result = calculate_fee(table, point, instrument, start, end, capacity_text, capacity_unit)
    if isinstance(result, FeeError):
        return result
    if result.currency != EUR:
        raise ValueError(f"{point.tso_name} bills in {result.currency}; the guarantee table is in EUR")
    ceghix = None
    if stage == BOOKED:
        ceghix = parse_ceghix(ceghix_text)
        if isinstance(ceghix, FeeError):
            return ceghix
    return rule(result, ceghix)
