"""
Pydantic schemas for Cart and CartItem.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pricing import PriceBreakdown


class CartItemAdd(BaseModel):
    variant_id: int
    quantity: int = Field(..., ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cart_id: int
    variant_id: int
    quantity: int
    price_snapshot: Optional[float] = None
    added_at: datetime

    # Populated by service layer when returning cart
    live_price: Optional[PriceBreakdown] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    size_label: Optional[str] = None
    primary_image_url: Optional[str] = None


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    session_token: Optional[str] = None
    items: list[CartItemRead] = []
    item_count: int = 0
    subtotal: float = 0.0
    created_at: datetime
    updated_at: datetime
