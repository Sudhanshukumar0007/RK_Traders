"""
Pydantic schemas for Order and OrderItem.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus, PaymentStatus


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: Optional[int] = None
    quantity: int
    unit_price: float
    total_price: float
    product_name_snapshot: Optional[str] = None
    sku_snapshot: Optional[str] = None
    size_label_snapshot: Optional[str] = None


class OrderCreate(BaseModel):
    """Request body for creating an order from the current cart."""
    shipping_address_id: int
    shipping_cost: float = Field(default=100.0)
    shipping_service: Optional[str] = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_address_id: Optional[int] = None
    subtotal: float
    shipping_cost: float
    total: float
    razorpay_order_id: Optional[str] = None
    awb_code: Optional[str] = None
    courier_name: Optional[str] = None
    tracking_status: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    items: list[OrderItemRead] = []
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    """Admin-only: update order status."""
    status: OrderStatus
