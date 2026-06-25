from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated
import razorpay
import hmac
import hashlib

from app.core.database import get_db
from app.core.config import settings
from app.models.order import Order, OrderStatus, PaymentStatus, OrderItem
from app.models.catalog import ProductVariant
from app.routers.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel

import uuid

router = APIRouter(prefix="/payments", tags=["Payments"])

RAZORPAY_KEY_ID = settings.RAZORPAY_KEY_ID
IS_MOCK = not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID == "rzp_test_placeholder"

if not IS_MOCK:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/{order_id}/create-razorpay-order")
async def create_razorpay_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Order already paid")

    amount_in_paise = int(order.total * 100)

    if IS_MOCK:
        mock_rzp_order_id = f"order_mock_{order.id}_{uuid.uuid4().hex[:8]}"
        order.razorpay_order_id = mock_rzp_order_id
        await db.commit()
        return {
            "razorpay_order_id": mock_rzp_order_id,
            "amount": amount_in_paise,
            "currency": "INR",
            "mock": True
        }

    try:
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order.order_number,
        }
        rzp_order = razorpay_client.order.create(data=data)
        
        order.razorpay_order_id = rzp_order["id"]
        await db.commit()
        
        return {"razorpay_order_id": rzp_order["id"], "amount": amount_in_paise, "currency": "INR", "key_id": settings.RAZORPAY_KEY_ID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Razorpay order: {str(e)}")

@router.post("/{order_id}/verify")
async def verify_razorpay_payment(
    order_id: int,
    payload: RazorpayVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.variant))
        .where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if payload.razorpay_order_id != order.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Razorpay order ID mismatch")
        
    if order.payment_status == PaymentStatus.PAID:
        return {"status": "success", "message": "Payment already verified"}
        
    # Verify signature
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        msg=f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(generated_signature, payload.razorpay_signature):
        order.payment_status = PaymentStatus.FAILED
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid payment signature")
        
    # Payment is valid
    order.payment_status = PaymentStatus.PAID
    order.status = OrderStatus.CONFIRMED
    order.razorpay_payment_id = payload.razorpay_payment_id
    
    # Decrement stock for the items atomically
    from sqlalchemy import update
    for item in order.items:
        stmt = (
            update(ProductVariant)
            .where(ProductVariant.id == item.variant_id, ProductVariant.stock_quantity >= item.quantity)
            .values(stock_quantity=ProductVariant.stock_quantity - item.quantity)
        )
        res = await db.execute(stmt)
        if res.rowcount != 1:
            await db.rollback()
            raise HTTPException(status_code=409, detail=f"Insufficient stock for variant {item.variant_id}")
            
    await db.commit()
    
    return {"status": "success", "message": "Payment verified and order confirmed"}
