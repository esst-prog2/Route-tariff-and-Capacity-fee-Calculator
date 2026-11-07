"""Bank Guarantee Calculator: the financial guarantee a TSO requires for one
capacity booking, at a capacity auction or for booked capacity.

Each TSO has its own rule in `GUARANTEE_RULES`; the public entry point is
`calculate_guarantee`, which returns a `GuaranteeResult` or a `FeeError`
carrying a message for the user. Amounts are exact until they are rounded
to cents, as on tab 2."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from fractions import Fraction
from typing import Callable

from .fee import GAS_YEAR, QUARTER, FeeError, FeeResult, calculate_fee
from .money import EUR, parse_number, round_minor, split_by_weights
from .points import EUSTREAM, Point
from .tariffs import TariffTable

AUCTION = "Capacity auction"  # the guarantee covers the capacity fee only
BOOKED = "Booked capacity"  # it also covers the GfON
STAGES = (AUCTION, BOOKED)

CEGHIX_MESSAGE = "CEGHIX must be a positive number."
CEGHIX_NOTE = "Enter the CEGHIX valid on the day before the booking."
SURCHARGE_MESSAGE = "The surcharge must be a percentage of 0 or more."
SURCHARGE_NOTE = "The auction surcharge (premium) in %, added to the tariff; leave it blank for none."

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
    surcharge: Fraction = Fraction(0)  # the auction surcharge in %, already included in `fee` and the amounts

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


def parse_surcharge(text) -> Fraction | FeeError:
    """A typed auction surcharge in %: blank means 0, else a number of 0 or more."""
    if text is None or str(text).strip() == "":
        return Fraction(0)
    try:
        surcharge = parse_number(text)
    except ValueError:
        return FeeError(SURCHARGE_MESSAGE)
    return surcharge if surcharge >= 0 else FeeError(SURCHARGE_MESSAGE)


def with_surcharge(result: FeeResult, surcharge: Fraction) -> FeeResult:
    """The fee with the auction surcharge: capacity x tariff + capacity x tariff x surcharge / 100, rounded
    to cents once; the invoice is split in the same proportions as without it, so it adds up to the total."""
    if surcharge == 0:
        return result
    exact_total = result.exact_total * (1 + surcharge / 100)
    total = round_minor(exact_total, result.currency)
    weights = [line.amount for line in result.invoice]
    if not any(weights):
        weights = [line.days for line in result.invoice]
    amounts = split_by_weights(total, weights)
    invoice = tuple(replace(line, amount=a) for line, a in zip(result.invoice, amounts))
    return replace(result, exact_total=exact_total, total=total, invoice=invoice)


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


EUSTREAM_NOTE = """**How Eustream sets the financial guarantee** (Operational Order valid from 24 July 2025, section 7.6; the English version is for information only, the Slovak one is binding)

**How much** (7.6.2). The guarantee is worked out separately for the capacity fee and for the neutrality charge (GfON), and the two are added together:
- **Gas year or quarter** (longer than two months): two months' payment, the two most expensive months of the capacity fee, and the GfON of the two longest months (62 days, or 61 for April to June).
- **Month or day** (shorter than two months): the whole payment, the whole capacity fee and the whole GfON of the product.
- **Capacity auction:** this tab counts only the capacity fee, including any auction surcharge; the GfON is added once the capacity is booked.
- GfON per day = capacity in kWh/h × 24 / 1000 × (CEGHIX + 1) × 0.85 / 100 EUR, using the CEGHIX of the day before the booking.

**When** (3.3.1, 4.2.12, 7.6.6). The capacity is allocated, and the contract signed, only once the guarantee is in place; under a framework contract Eustream does not allocate a booking that would leave the guarantee below the required amount. At points to and from third countries and the domestic point, the guarantee is due within 15 calendar days of the request for annual and longer contracts and 7 days for short-term ones, and at least 3 business days before transmission starts.

**How long** (7.6.7, 7.6.9). A bank guarantee must be irrevocable and expire **no earlier than two months after the end of the contract**. The user keeps the guarantee at the required level for the whole contract; if Eustream draws on it, the user tops it up within **3 calendar days** (not needed when the guarantee already covers the whole payment). After all obligations are settled, Eustream pays back any unused pre-payment or cash collateral.

**Forms** (7.6.6): bank guarantee, pre-payment or cash collateral. Eustream may ask for a different amount after a credit check (7.6.5) and may reassess it during the contract (7.6.4); the imbalance guarantee (7.6.3) is not covered here.
"""

# Each supported TSO's guarantee rules in words, shown on tab 3 when the TSO is chosen.
GUARANTEE_NOTES: dict[str, str] = {
    EUSTREAM: EUSTREAM_NOTE,
}


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
    surcharge_text=None,
) -> GuaranteeResult | FeeError:
    """The guarantee for one booking at `point` (a TSO in `GUARANTEE_RULES`); `ceghix_text`
    is read only for booked capacity. The auction surcharge (`surcharge_text`, in %) raises the
    capacity fee and so its guarantee, at either stage; the GfON does not depend on it."""
    if stage not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}")
    rule = GUARANTEE_RULES[point.tso]
    result = calculate_fee(table, point, instrument, start, end, capacity_text, capacity_unit)
    if isinstance(result, FeeError):
        return result
    if result.currency != EUR:
        raise ValueError(f"{point.tso_name} bills in {result.currency}; the guarantee table is in EUR")
    surcharge = parse_surcharge(surcharge_text)
    if isinstance(surcharge, FeeError):
        return surcharge
    result = with_surcharge(result, surcharge)
    ceghix = None
    if stage == BOOKED:
        ceghix = parse_ceghix(ceghix_text)
        if isinstance(ceghix, FeeError):
            return ceghix
    return replace(rule(result, ceghix), surcharge=surcharge)
