from datetime import date
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.catalog import ProductVariant
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.user import User, Address
from app.routers.auth import get_current_user, get_current_admin
from app.routers.cart import get_variant_price
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])



async def generate_order_number(db: AsyncSession) -> str:
    """Generates an atomic, sequential order number per day: SHP-YYYYMMDD-XXXX."""
    today = date.today()
    stmt = text(
        "INSERT INTO daily_order_counters (date, last_number) "
        "VALUES (:today, 1) "
        "ON CONFLICT (date) DO UPDATE "
        "SET last_number = daily_order_counters.last_number + 1 "
        "RETURNING last_number"
    )
    result = await db.execute(stmt, {"today": today})
    last_number = result.scalar_one()

    date_str = today.strftime("%Y%m%d")
    return f"SHP-{date_str}-{last_number:04d}"


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Fetch user's cart and check if it's empty
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
        )
        .where(Cart.user_id == current_user.id)
    )
    cart = result.scalar_one_or_none()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot place order with an empty cart",
        )

    # Validate shipping address belongs to user
    result = await db.execute(
        select(Address).where(
            Address.id == order_in.shipping_address_id, Address.user_id == current_user.id
        )
    )
    shipping_address = result.scalar_one_or_none()
    if not shipping_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shipping address",
        )

    # Validate stock availability for all items in cart before committing
    for item in cart.items:
        if item.quantity > item.variant.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for variant {item.variant.sku}. Requested: {item.quantity}, Available: {item.variant.stock_quantity}",
            )

    # Generate sequential unique order number
    order_number = await generate_order_number(db)

    # Create Order record
    db_order = Order(
        user_id=current_user.id,
        order_number=order_number,
        status=OrderStatus.PENDING_PAYMENT,
        payment_status=PaymentStatus.PENDING,
        shipping_address_id=shipping_address.id,
        subtotal=0.0,
        shipping_cost=order_in.shipping_cost,
        courier_name=order_in.shipping_service,
        total=0.0,
    )
    db.add(db_order)
    await db.flush()  # Populates db_order.id

    subtotal = 0.0
    for item in cart.items:
        price_breakdown = get_variant_price(
            item.variant, item.quantity, current_user.is_wholesale_customer
        )
        subtotal += price_breakdown.total_price

        # Snapshot product details for historical consistency
        db_item = OrderItem(
            order_id=db_order.id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            unit_price=price_breakdown.unit_price,
            total_price=price_breakdown.total_price,
            product_name_snapshot=item.variant.product.name,
            sku_snapshot=item.variant.sku,
            size_label_snapshot=item.variant.size_label,
        )
        db.add(db_item)

    db_order.subtotal = subtotal
    db_order.total = subtotal + db_order.shipping_cost

    # Empty cart items
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))

    await db.commit()
    await db.refresh(db_order)

    # Return completed order with items pre-loaded
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == db_order.id)
    )
    return result.scalar_one()


@router.get("", response_model=list[OrderRead])
async def list_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 10,
    offset: int = 0,
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/{order_number}", response_model=OrderRead)
async def get_order_detail(
    order_number: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.order_number == order_number)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Authenticated user can view their own order; admin can view any order
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return order


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.variant))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    old_status = order.status
    new_status = status_in.status

    # Define which statuses represent stock having been decremented
    DECREMENTED_STATUSES = {
        OrderStatus.CONFIRMED,
        OrderStatus.PROCESSING,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
    }

    # Transitioning into a decremented status from a non-decremented status
    if old_status not in DECREMENTED_STATUSES and new_status in DECREMENTED_STATUSES:
        # Decrement stock for all items
        for item in order.items:
            if item.variant:
                if item.variant.stock_quantity < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot confirm order. Insufficient stock for variant {item.sku_snapshot or item.variant.sku}.",
                    )
                item.variant.stock_quantity -= item.quantity

    # Transitioning back to a non-decremented status (or cancelled) from a decremented status
    elif old_status in DECREMENTED_STATUSES and new_status not in DECREMENTED_STATUSES:
        # Restore stock for all items
        for item in order.items:
            if item.variant:
                item.variant.stock_quantity += item.quantity

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order
