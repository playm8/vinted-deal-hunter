"""
Recognising a listing that got cheaper.

An item used to be notified once and never looked at again, so a seller
dropping their price by a third three days later went unnoticed — which is
exactly the moment worth knowing about.

The rules here exist to keep that from becoming noise. A drop is measured
against a baseline that only moves when a drop is announced, never against the
last price seen: otherwise a seller nudging a price down repeatedly would alert
on every cycle, and one moving it up and down would alert forever.
"""

import db
from logger import get_logger

logger = get_logger(__name__)


def is_enabled():
    return str(db.get_parameter("price_drop_enabled")).lower() == "true"


def _number(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_price(value):
    """
    Read a price that may arrive as a string.

    The API returns prices as strings and the column is NUMERIC, so both forms
    turn up depending on whether a value came from Vinted or from the database.

    Args:
        value: Whatever holds the price.

    Returns:
        float | None: The price, or None when it cannot be read.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_drop(known_row, new_price, now):
    """
    Decide whether a known item just became worth mentioning again.

    Args:
        known_row (dict): The stored row, with drop_baseline_price,
            first_price and drop_notified_at.
        new_price (float): The price seen right now.
        now (float): Current timestamp.

    Returns:
        dict | None: {"baseline", "new_price", "drop_pct", "drop_amount"} when
            a drop should be announced, None otherwise.
    """
    if not is_enabled():
        return None

    baseline = to_price(known_row.get("drop_baseline_price"))
    if baseline is None:
        baseline = to_price(known_row.get("first_price"))
    if baseline is None or baseline <= 0 or new_price is None or new_price <= 0:
        return None

    drop_amount = baseline - new_price
    if drop_amount <= 0:
        # The price went up or did not move. The baseline stays where it is:
        # raising it would let an oscillating price alert again and again.
        return None

    drop_pct = drop_amount / baseline * 100
    min_pct = _number(db.get_parameter("price_drop_min_pct"), 10)
    min_amount = _number(db.get_parameter("price_drop_min_amount"), 3)

    # Both thresholds must be met. The absolute one is what stops small prices
    # from being noisy: without it 8 EUR to 7 EUR is a 12.5% drop.
    if drop_pct < min_pct or drop_amount < min_amount:
        return None

    cooldown = _number(db.get_parameter("price_drop_cooldown_hours"), 24) * 3600
    last_notified = to_price(known_row.get("drop_notified_at")) or 0
    if last_notified and now - last_notified < cooldown:
        return None

    return {
        "baseline": round(baseline, 2),
        "new_price": round(new_price, 2),
        "drop_pct": round(drop_pct),
        "drop_amount": round(drop_amount, 2),
    }


def max_per_cycle():
    """How many drops may be announced in one pass, so a sale cannot flood."""
    return int(_number(db.get_parameter("price_drop_max_per_cycle"), 5))
