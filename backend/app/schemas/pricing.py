"""
Pydantic schema for the pricing service output.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PriceBreakdown(BaseModel):
    """
    Returned by the pricing service for a given variant + quantity combination.
    """
    variant_id: int
    quantity: int

    unit_price: float          # Price per unit at this quantity
    total_price: float         # unit_price × quantity

    mrp: float                 # Always the retail price, for reference
    wholesale_price: Optional[float] = None
    wholesale_min_qty: Optional[int] = None

    tier_applied: str          # "retail" | "wholesale"
    savings_amount: float = 0.0     # Total savings vs MRP (0 if retail)
    savings_percentage: float = 0.0  # e.g. 12.5 for 12.5% off
    wholesale_units_away: Optional[int] = None  # How many more units to hit wholesale (if not there yet)
