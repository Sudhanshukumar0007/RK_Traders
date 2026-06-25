"""
Order and OrderItem models.
Prices are snapshotted at order creation time — never reference live prices for historical orders.
"""

from __future__ import annotations

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"   # Created, awaiting payment
    PENDING = "pending"                   # Payment received, not yet processed
    CONFIRMED = "confirmed"               # Confirmed by staff
    PROCESSING = "processing"             # Being picked/packed
    SHIPPED = "shipped"                   # Handed to courier
    DELIVERED = "delivered"               # Confirmed delivered
    CANCELLED = "cancelled"               # Cancelled before ship


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Human-readable, e.g. SHP-20260615-0001
    order_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING_PAYMENT,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    shipping_address_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True
    )

    # Financials (all in INR)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    shipping_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # Payment gateway fields (Phase 6)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Shipping / logistics fields (Phase 5)
    awb_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    courier_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    shipping_label_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tracking_status: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Stock reservation expiry (Phase 6 — release if payment not completed in time)
    reservation_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="orders"
    )
    shipping_address: Mapped[Optional["Address"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Address", back_populates="orders"
    )
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        Index("ix_orders_created_at", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Price snapshot — locked in at order creation, never changes
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Snapshot of product info in case the product is later deleted/renamed
    product_name_snapshot: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sku_snapshot: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_label_snapshot: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    variant: Mapped[Optional["ProductVariant"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ProductVariant", back_populates="order_items"
    )


class DailyOrderCounter(Base):
    __tablename__ = "daily_order_counters"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
