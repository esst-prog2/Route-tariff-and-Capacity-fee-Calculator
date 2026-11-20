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

from .fee import DAY, GAS_YEAR, MONTH, QUARTER, FeeError, FeeResult, calculate_fee
from .money import EUR, parse_number, round_minor, split_by_weights
from .points import ENTRY, EUSTREAM, GCA, Point
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
    """Amounts in cents of `currency`; the GfON fields are None at a capacity auction and for a
    TSO without a GfON, the capacity fee guarantee is None when the TSO asks for none (a GCA day)."""

    fee: FeeResult
    capacity_fee: int
    capacity_fee_guarantee: int | None
    gfon_fee: int | None = None
    gfon_fee_guarantee: int | None = None
    surcharge: Fraction = Fraction(0)  # the auction surcharge in %, already included in `fee` and the amounts
    commodity_fee: int | None = None  # GCA's commodity charge; None for a TSO without one
    commodity_fee_guarantee: int | None = None

    @property
    def currency(self) -> str:
        return self.fee.currency

    @property
    def total_guarantee(self) -> int | None:
        """The sum of the guarantees, None counting as 0; None when none is required."""
        parts = (self.capacity_fee_guarantee, self.gfon_fee_guarantee, self.commodity_fee_guarantee)
        if all(part is None for part in parts):
            return None
        return sum(part or 0 for part in parts)


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

# GTC IV para. 15: how many of the first monthly invoices the security deposit covers (None = all of them).
GCA_FIRST_MONTHS = {MONTH: None, QUARTER: 2, GAS_YEAR: 3}

# GCA's commodity charge in EUR/MWh, from each date on: (valid from, entry rate, exit rate). Every change
# falls on the first of a month. Before the first date no rate is known and the charge counts as 0.
GCA_COMMODITY_RATES = (
    (date(2026, 1, 1), Fraction("0.03322"), Fraction("0.11963")),
    (date(2027, 1, 1), Fraction("0.07914"), Fraction("0.2586")),
)


def gca_commodity_rate(day: date, direction: str) -> Fraction:
    """The commodity charge in EUR/MWh valid on `day` at an entry or exit point; 0 before 1 January 2026."""
    rate = Fraction(0)
    for valid_from, entry, exit_ in GCA_COMMODITY_RATES:
        if day >= valid_from:
            rate = entry if direction == ENTRY else exit_
    return rate


def gca_commodity(result: FeeResult, lines) -> Fraction:
    """The exact commodity charge for invoice `lines`: full use of the capacity, 24 hours every gas day
    (kWh/d x days / 1000 = MWh), at the rate valid in each month."""
    return sum((result.capacity_kwh_d * line.days / 1000 * gca_commodity_rate(date(line.year, line.month, 1),
                                                                               result.point.direction)
                for line in lines), Fraction(0))


def gca_guarantee(result: FeeResult, ceghix: Fraction | None = None) -> GuaranteeResult:
    """Gas Connect Austria, GTC chapter IV para. 15: the fee of the first months of the service
    (a month: all of it; a quarter: the first two; a gas year: the first three), taken from the
    monthly invoice, plus the commodity charge on the volume of those months; no security deposit
    for a day, which the activation deposit covers. No GfON."""
    invoice = sorted(result.invoice, key=lambda line: (line.year, line.month))
    commodity = round_minor(gca_commodity(result, invoice), result.currency)
    if result.instrument == DAY:
        return GuaranteeResult(result, result.total, None, commodity_fee=commodity)
    covered = invoice[:GCA_FIRST_MONTHS[result.instrument]]
    guarantee = sum(line.amount for line in covered)
    commodity_guarantee = round_minor(gca_commodity(result, covered), result.currency)
    return GuaranteeResult(result, result.total, guarantee, commodity_fee=commodity,
                           commodity_fee_guarantee=commodity_guarantee)


GCA_NOTE = """**How Gas Connect Austria sets the security deposit** (General Terms and Conditions for Transmission Network Access, Annex 1 to the Frame Capacity Contract, version of 23 September 2013, chapter IV; the English version is for information only, the German one is binding)

**How much** (IV.15). The deposit depends on the term of the capacity contract, excluding the bank fees:
- **Month:** the whole fee for the service.
- **Quarter:** the fee for the **first two months** of the service.
- **Gas year:** the fee for the **first three months** of the service.
- **Day:** no security deposit; contracts of one day or less are covered by the activation deposit.
- This tab takes the fee from the monthly invoices, including any auction surcharge.

**Commodity charge.** The guarantee also covers GCA's commodity charge for the same months: the volume at full use of the capacity (capacity in kWh/h × 24 × days / 1000 MWh) times the rate in EUR/MWh. From 1 January 2026 it is **0.03322 at entry and 0.11963 at exit** points; from 1 January 2027 **0.07914 at entry and 0.2586 at exit**. No rate is known before 1 January 2026, so earlier months count as 0. The auction surcharge does not apply to it.

**Activation deposit** (IV.6–10). Before taking part in GCA's auctions, the user provides a one-off activation deposit of **EUR 100,000**: a bank guarantee unlimited in time (on GCA's sample) or a cash deposit, received at least **5 working days** before the first auction, and again after it has been drawn on. It must be kept at the full amount at all times, covers contracts of one day or less, and GCA may adjust the amount. It is not included in this tab's totals.

**When** (IV.13–14). The security deposit must be received no later than **5 working days after the capacity contract is concluded**.

**How long** (IV.13–14). The bank guarantee is returned, and the cash deposit repaid without interest, once the obligations under the capacity contract have been fully met.

**If missed** (IV.16). GCA may claim the activation deposit up to its full amount, the capacity contract ends at once, and the user may not take part in auctions again until it has met its obligations in full.

**Forms** (IV.12): bank guarantee (on GCA's sample) or cash deposit, at the user's choice.
"""

GCA_DAY_NOTE = ("Gas Connect Austria asks no security deposit for day contracts: they are covered by its one-off "
                "activation deposit of EUR 100,000, which is not included in the total.")

# Each supported TSO's guarantee rules in words, shown on tab 3 when the TSO is chosen.
GUARANTEE_NOTES: dict[str, str] = {
    EUSTREAM: EUSTREAM_NOTE,
    GCA: GCA_NOTE,
}


GUARANTEE_RULES: dict[str, Callable[[FeeResult, Fraction | None], GuaranteeResult]] = {
    EUSTREAM: eustream_guarantee,
    GCA: gca_guarantee,
}

# TSOs whose guarantee depends on the stage (and, once booked, on the CEGHIX); tab 3 asks for both only for them.
STAGED_TSOS = frozenset({EUSTREAM})


def is_gca_day(point: Point, instrument: str) -> bool:
    """A booking for which GCA asks no security deposit, so tab 3 shows the activation deposit note."""
    return point.tso == GCA and instrument == DAY


def calculate_guarantee(
    table: TariffTable,
    point: Point,
    instrument: str,
    start: date,
    end: date,
    capacity_text,
    capacity_unit: str,
    stage: str | None,
    ceghix_text=None,
    surcharge_text=None,
) -> GuaranteeResult | FeeError:
    """The guarantee for one booking at `point` (a TSO in `GUARANTEE_RULES`); `ceghix_text`
    is read only for booked capacity. The auction surcharge (`surcharge_text`, in %) raises the
    capacity fee and so its guarantee, at either stage; the GfON does not depend on it.
    The stage matters only for a TSO in `STAGED_TSOS`; for the others it and the CEGHIX are ignored."""
    staged = point.tso in STAGED_TSOS
    if staged and stage not in STAGES:
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
    if staged and stage == BOOKED:
        ceghix = parse_ceghix(ceghix_text)
        if isinstance(ceghix, FeeError):
            return ceghix
    return replace(rule(result, ceghix), surcharge=surcharge)
