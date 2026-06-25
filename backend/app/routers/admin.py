from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Annotated

from app.core.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.catalog import Product, ProductVariant
from app.routers.auth import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/metrics")
async def get_dashboard_metrics(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    total_revenue_result = await db.execute(select(func.sum(Order.total)))
    total_revenue = total_revenue_result.scalar_one_or_none() or 0.0

    total_orders_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_orders_result.scalar_one_or_none() or 0

    total_customers_result = await db.execute(select(func.count(User.id)))
    total_customers = total_customers_result.scalar_one_or_none() or 0

    total_products_result = await db.execute(select(func.count(Product.id)))
    total_products = total_products_result.scalar_one_or_none() or 0

    return {
        "total_revenue": float(total_revenue),
        "total_orders": int(total_orders),
        "total_customers": int(total_customers),
        "total_products": int(total_products),
    }

@router.get("/orders")
async def list_all_orders(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.user))
        .order_by(Order.created_at.desc())
        .limit(100)
    )
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": o.user.name if o.user else "Unknown",
            "total": float(o.total),
            "status": o.status.value,
            "payment_status": o.payment_status.value,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]
