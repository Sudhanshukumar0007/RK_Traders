"""
Catalog models: Category, Brand, Product, ProductVariant, ProductImage, ProductAttribute
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Category ────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Self-referential relationship
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")

    __table_args__ = (
        Index("ix_categories_parent_id_active", "parent_id", "is_active"),
    )


# ─── Brand ───────────────────────────────────────────────────────────────────

class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="brand")


# ─── Product ─────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(550), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    brand_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Hardware-specific classification fields
    component_type: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, index=True
    )  # e.g. "Reducer Bush", "Elbow", "Tee"
    material: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, index=True
    )  # e.g. "UPVC", "CPVC", "GI"
    pressure_rating: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # e.g. "SCH-40", "SCH-80"

    # SEO fields
    meta_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Full-text search vector (populated via trigger in migration)
    search_vector = Column(TSVECTOR, nullable=True)

    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    brand: Mapped[Optional["Brand"]] = relationship("Brand", back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    attributes: Mapped[list["ProductAttribute"]] = relationship(
        "ProductAttribute", back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_products_component_type_material", "component_type", "material"),
        Index("ix_products_pressure_rating", "pressure_rating"),
        Index("ix_products_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_products_active_category", "is_active", "category_id"),
    )


# ─── ProductVariant ──────────────────────────────────────────────────────────

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Size / dimension info
    size_label: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g. "1½ x 1¼", "2 x 1"
    size_dimensions: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {outer_dia, inner_dia, length, unit}
    dimensions_cm: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {length, width, height} — for volumetric shipping

    weight_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Pricing
    mrp: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    wholesale_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    wholesale_min_qty: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # quantity threshold to trigger wholesale

    # Inventory
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # For Phase 6 stock reservation
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    images: Mapped[list["ProductImage"]] = relationship("ProductImage", back_populates="variant")
    cart_items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="variant")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="variant")

    __table_args__ = (
        Index("ix_variants_product_active", "product_id", "is_active"),
        Index("ix_variants_stock", "stock_quantity"),
    )


# ─── ProductImage ────────────────────────────────────────────────────────────

class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="images")
    variant: Mapped[Optional["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="images"
    )

    __table_args__ = (
        Index("ix_images_product_primary", "product_id", "is_primary"),
    )


# ─── ProductAttribute ────────────────────────────────────────────────────────

class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attribute_name: Mapped[str] = mapped_column(String(200), nullable=False)
    attribute_value: Mapped[str] = mapped_column(String(500), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="attributes")

    __table_args__ = (
        Index("ix_attributes_product_name", "product_id", "attribute_name"),
    )
