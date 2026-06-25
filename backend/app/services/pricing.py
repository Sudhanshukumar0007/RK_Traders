"""
Pricing service — calculates unit price, totals, and savings for a given variant + quantity.

The business rule:
- If quantity < variant.wholesale_min_qty (or wholesale not configured): use MRP
- If quantity >= variant.wholesale_min_qty AND wholesale_price is set: use wholesale_price

This function is the single source of truth for all price calculations across the app
(cart, product page, order creation).
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.schemas.pricing import PriceBreakdown


def calculate_price(
    *,
    variant_id: int,
    quantity: int,
    mrp: float,
    wholesale_price: Optional[float],
    wholesale_min_qty: Optional[int],
) -> PriceBreakdown:
    """
    Pure function — no DB calls. All inputs come from the variant record.

    Args:
        variant_id: For reference in the returned schema.
        quantity: How many units are being priced.
        mrp: Retail price per unit.
        wholesale_price: Optional discounted price per unit for bulk orders.
        wholesale_min_qty: Minimum quantity to activate wholesale_price.

    Returns:
        PriceBreakdown with all pricing context for the frontend.
    """
    if quantity < 1:
        raise ValueError("quantity must be >= 1")

    # Determine which tier applies
    wholesale_available = (
        wholesale_price is not None
        and wholesale_min_qty is not None
        and wholesale_price > 0
        and wholesale_min_qty > 0
    )

    use_wholesale = wholesale_available and quantity >= wholesale_min_qty  # type: ignore[operator]

    unit_price = wholesale_price if use_wholesale else mrp
    tier = "wholesale" if use_wholesale else "retail"

    total_price = _round(unit_price * quantity)
    mrp_total = _round(mrp * quantity)
    savings_amount = _round(mrp_total - total_price) if use_wholesale else 0.0
    savings_pct = _round((savings_amount / mrp_total) * 100) if mrp_total > 0 and use_wholesale else 0.0

    units_away: Optional[int] = None
    if wholesale_available and not use_wholesale:
        units_away = wholesale_min_qty - quantity  # type: ignore[operator]

    return PriceBreakdown(
        variant_id=variant_id,
        quantity=quantity,
        unit_price=_round(unit_price),
        total_price=total_price,
        mrp=_round(mrp),
        wholesale_price=_round(wholesale_price) if wholesale_price is not None else None,
        wholesale_min_qty=wholesale_min_qty,
        tier_applied=tier,
        savings_amount=savings_amount,
        savings_percentage=savings_pct,
        wholesale_units_away=units_away,
    )


def _round(value: float) -> float:
    """Round to 2 decimal places using ROUND_HALF_UP (standard for currency)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
