"""
Shipping router: quote, ship, track, and Shiprocket webhook.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.order import Order
from app.models.cart import Cart, CartItem
from app.models.catalog import ProductVariant
from app.services.shipping import (
    billable_weight_kg,
    get_shipping_quotes,
    create_shipment,
    get_tracking_info,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shipping", tags=["shipping"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class QuoteRequest(BaseModel):
    pincode: str
    cart_id: Optional[int] = None
    order_id: Optional[int] = None
    cod: bool = False


class ShipRequest(BaseModel):
    order_id: int


# ─── POST /api/shipping/quote ─────────────────────────────────────────────────

@router.post("/quote")
async def get_quote(
    payload: QuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Return available courier options with cost estimates for a pincode.
    Works for both cart (guest/auth) and confirmed orders.
    """
    if len(payload.pincode) != 6 or not payload.pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode — must be 6 digits")

    # Build item list for weight calculation
    items_for_weight: list[dict] = []

    if payload.cart_id:
        result = await db.execute(
            select(CartItem, ProductVariant)
            .join(ProductVariant, CartItem.variant_id == ProductVariant.id)
            .where(CartItem.cart_id == payload.cart_id)
        )
        for cart_item, variant in result.all():
            items_for_weight.append({
                "quantity": cart_item.quantity,
                "weight_grams": variant.weight_grams or 200,
                "dimensions_cm": variant.dimensions_cm or {},
            })

    elif payload.order_id:
        from app.models.order import OrderItem
        result = await db.execute(
            select(OrderItem, ProductVariant)
            .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
            .where(OrderItem.order_id == payload.order_id)
        )
        for order_item, variant in result.all():
            items_for_weight.append({
                "quantity": order_item.quantity,
                "weight_grams": variant.weight_grams or 200,
                "dimensions_cm": variant.dimensions_cm or {},
            })

    # Default: minimum weight if nothing to calculate from
    weight_kg = billable_weight_kg(items_for_weight) if items_for_weight else 0.5

    quotes = await get_shipping_quotes(payload.pincode, weight_kg, payload.cod)
    return {"pincode": payload.pincode, "weight_kg": weight_kg, "quotes": quotes}


# ─── POST /api/orders/{order_id}/ship ────────────────────────────────────────

@router.post("/ship/{order_id}")
async def ship_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin: create shipment in Shiprocket and update order with AWB."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.awb_code:
        return {"message": "Order already shipped", "awb_code": order.awb_code}

    # Build Shiprocket order payload
    ship_data = await _build_shiprocket_order(order, db)
    result_data = await create_shipment(ship_data)

    # Update order fields
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(
            awb_code=result_data.get("awb_code"),
            courier_name=result_data.get("courier_name"),
            shipping_label_url=result_data.get("label_url"),
            status="shipped",
        )
    )
    await db.commit()

    return result_data


async def _build_shiprocket_order(order: Order, db: AsyncSession) -> dict:
    """Build the payload expected by Shiprocket's create order API."""
    from app.models.order import OrderItem
    from app.models.catalog import Product

    items_result = await db.execute(
        select(OrderItem, ProductVariant, Product)
        .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(OrderItem.order_id == order.id)
    )

    shiprocket_items = []
    for oi, variant, product in items_result.all():
        dims = variant.dimensions_cm or {}
        shiprocket_items.append({
            "name": f"{product.name} - {variant.size_label}",
            "sku": variant.sku,
            "units": oi.quantity,
            "selling_price": str(oi.unit_price),
            "discount": "",
            "tax": "",
            "hsn": "",
        })

    addr = order.shipping_address or {}
    return {
        "order_id": order.order_number,
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "pickup_location": "Primary",
        "billing_customer_name": addr.get("full_address", "")[:50],
        "billing_address": addr.get("full_address", ""),
        "billing_city": addr.get("city", ""),
        "billing_pincode": addr.get("pincode", ""),
        "billing_state": addr.get("state", ""),
        "billing_country": "India",
        "billing_phone": addr.get("phone", ""),
        "shipping_is_billing": True,
        "order_items": shiprocket_items,
        "payment_method": "Prepaid",
        "sub_total": float(order.subtotal),
        "length": 20,
        "breadth": 15,
        "height": 10,
        "weight": 0.5,
    }


# ─── GET /api/orders/{order_number}/tracking ─────────────────────────────────

@router.get("/track/{order_number}")
async def track_order(
    order_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(
            Order.order_number == order_number,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.awb_code:
        return {
            "status": order.status,
            "awb_code": None,
            "message": "Shipment not yet created",
        }

    tracking = await get_tracking_info(order.awb_code)
    return {
        "order_number": order_number,
        "awb_code": order.awb_code,
        "courier_name": order.courier_name,
        **tracking,
    }


# ─── POST /api/webhooks/shiprocket ────────────────────────────────────────────

SHIPROCKET_STATUS_MAP = {
    "Delivered": "delivered",
    "In Transit": "shipped",
    "Out for Delivery": "shipped",
    "Pickup Scheduled": "processing",
    "Pickup Cancelled": "processing",
    "RTO Initiated": "cancelled",
    "RTO Delivered": "cancelled",
}

@router.post("/webhooks/shiprocket", include_in_schema=False)
async def shiprocket_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive shipment status updates from Shiprocket.
    Shiprocket sends JSON with the AWB and new status.
    """
    body = await request.body()

    # Signature verification (optional — Shiprocket doesn't always send one)
    webhook_secret = request.headers.get("X-Shiprocket-Signature", "")
    if webhook_secret:
        expected = hmac.new(
            "shiprocket_webhook_secret".encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, webhook_secret):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        data = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    awb = data.get("awb") or data.get("awb_code")
    sr_status = data.get("current_status") or data.get("status")

    if not awb or not sr_status:
        return {"status": "ignored", "reason": "missing awb or status"}

    # Map to internal status
    internal_status = SHIPROCKET_STATUS_MAP.get(sr_status)

    result = await db.execute(select(Order).where(Order.awb_code == awb))
    order = result.scalar_one_or_none()

    if not order:
        return {"status": "ignored", "reason": "order not found for AWB"}

    update_vals: dict = {"tracking_status": sr_status}
    if internal_status:
        update_vals["status"] = internal_status

    await db.execute(update(Order).where(Order.awb_code == awb).values(**update_vals))
    await db.commit()

    logger.info("Webhook: order %s updated to %s (AWB %s)", order.order_number, sr_status, awb)
    return {"status": "ok", "order": order.order_number}
