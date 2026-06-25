"""
Pydantic schemas for catalog entities.
Follows the multi-model pattern: Create, Update, Read variants for each entity.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─── Category ────────────────────────────────────────────────────────────────

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=220)
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=220)
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CategoryTree(CategoryRead):
    """Category with nested children for hierarchical responses."""
    children: list["CategoryTree"] = []


CategoryTree.model_rebuild()


# ─── Brand ───────────────────────────────────────────────────────────────────

class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=220)
    logo_url: Optional[str] = None
    is_active: bool = True


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=220)
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class BrandRead(BrandBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ─── ProductImage ────────────────────────────────────────────────────────────

class ProductImageCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    image_url: str
    alt_text: Optional[str] = None
    display_order: int = 0
    is_primary: bool = False


class ProductImageRead(ProductImageCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ─── ProductAttribute ────────────────────────────────────────────────────────

class ProductAttributeCreate(BaseModel):
    product_id: int
    attribute_name: str = Field(..., max_length=200)
    attribute_value: str = Field(..., max_length=500)


class ProductAttributeRead(ProductAttributeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ─── ProductVariant ──────────────────────────────────────────────────────────

class ProductVariantBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    size_label: Optional[str] = Field(None, max_length=100)
    size_dimensions: Optional[dict[str, Any]] = None
    dimensions_cm: Optional[dict[str, Any]] = None
    weight_grams: Optional[int] = None
    mrp: float = Field(..., gt=0)
    wholesale_price: Optional[float] = Field(None, gt=0)
    wholesale_min_qty: Optional[int] = Field(None, gt=0)
    stock_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    product_id: int


class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    size_label: Optional[str] = Field(None, max_length=100)
    size_dimensions: Optional[dict[str, Any]] = None
    dimensions_cm: Optional[dict[str, Any]] = None
    weight_grams: Optional[int] = None
    mrp: Optional[float] = Field(None, gt=0)
    wholesale_price: Optional[float] = Field(None, gt=0)
    wholesale_min_qty: Optional[int] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductVariantRead(ProductVariantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    reserved_quantity: int
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageRead] = []

    @property
    def available_stock(self) -> int:
        return max(0, self.stock_quantity - self.reserved_quantity)


# ─── Product ─────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=550)
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    component_type: Optional[str] = Field(None, max_length=200)
    material: Optional[str] = Field(None, max_length=200)
    pressure_rating: Optional[str] = Field(None, max_length=50)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=400)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    slug: Optional[str] = Field(None, min_length=1, max_length=550)
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    component_type: Optional[str] = Field(None, max_length=200)
    material: Optional[str] = Field(None, max_length=200)
    pressure_rating: Optional[str] = Field(None, max_length=50)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=400)
    is_active: Optional[bool] = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryRead] = None
    brand: Optional[BrandRead] = None
    variants: list[ProductVariantRead] = []
    images: list[ProductImageRead] = []
    attributes: list[ProductAttributeRead] = []


class ProductListItem(BaseModel):
    """Lightweight product schema for list/grid views — no variants detail, just price range."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    component_type: Optional[str] = None
    material: Optional[str] = None
    pressure_rating: Optional[str] = None
    is_active: bool
    category: Optional[CategoryRead] = None
    brand: Optional[BrandRead] = None
    primary_image_url: Optional[str] = None
    min_price: Optional[float] = None   # populated by service layer
    max_price: Optional[float] = None
    variant_count: int = 0
    created_at: datetime
