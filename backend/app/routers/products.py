"""
Products router — endpoints for retrieving products, details, variants, and pricing.
"""

from __future__ import annotations

from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.catalog import Product, ProductVariant, ProductImage, Category, Brand, ProductAttribute
from app.schemas.catalog import ProductRead, ProductListItem, ProductVariantRead
from app.schemas.pricing import PriceBreakdown
from app.services.pricing import calculate_price

router = APIRouter(prefix="/products", tags=["products"])

class ProductDetailResponse(BaseModel):
    product: ProductRead
    related_products: list[ProductListItem]

@router.get("", response_model=list[ProductListItem])
async def get_products(
    category_id: Optional[int] = Query(None, description="Filter by Category ID"),
    brand_id: Optional[int] = Query(None, description="Filter by Brand ID"),
    component_type: Optional[str] = Query(None, description="Filter by Component Type"),
    pressure_rating: Optional[str] = Query(None, description="Filter by Pressure Rating"),
    material: Optional[str] = Query(None, description="Filter by Material"),
    min_price: Optional[float] = Query(None, description="Filter by Minimum MRP"),
    max_price: Optional[float] = Query(None, description="Filter by Maximum MRP"),
    sort_by: str = Query("newest", description="Sort by: price_asc, price_desc, newest, name_asc"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a paginated, filtered, sorted list of products with metadata.
    """
    # Subquery to aggregate variant details per product
    var_sub = (
        select(
            ProductVariant.product_id,
            func.min(ProductVariant.mrp).label("min_price"),
            func.max(ProductVariant.mrp).label("max_price"),
            func.count(ProductVariant.id).label("variant_count")
        )
        .where(ProductVariant.is_active == True)
        .group_by(ProductVariant.product_id)
        .subquery()
    )

    # Base query selecting Product and aggregates
    stmt = (
        select(
            Product,
            var_sub.c.min_price,
            var_sub.c.max_price,
            var_sub.c.variant_count,
            ProductImage.image_url.label("primary_image_url")
        )
        .join(var_sub, Product.id == var_sub.c.product_id)
        .outerjoin(
            ProductImage,
            and_(Product.id == ProductImage.product_id, ProductImage.is_primary == True)
        )
        .options(
            selectinload(Product.category),
            selectinload(Product.brand)
        )
        .where(Product.is_active == True)
    )

    # Apply filters
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if brand_id is not None:
        stmt = stmt.where(Product.brand_id == brand_id)
    if component_type is not None:
        stmt = stmt.where(Product.component_type == component_type)
    if pressure_rating is not None:
        stmt = stmt.where(Product.pressure_rating == pressure_rating)
    if material is not None:
        stmt = stmt.where(Product.material == material)
    if min_price is not None:
        stmt = stmt.where(var_sub.c.min_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(var_sub.c.max_price <= max_price)

    # Apply sorting
    if sort_by == "price_asc":
        stmt = stmt.order_by(var_sub.c.min_price.asc())
    elif sort_by == "price_desc":
        stmt = stmt.order_by(var_sub.c.max_price.desc())
    elif sort_by == "name_asc":
        stmt = stmt.order_by(Product.name.asc())
    else:  # newest
        stmt = stmt.order_by(Product.created_at.desc())

    # Paginate
    stmt = stmt.limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    rows = result.all()

    list_items = []
    for row in rows:
        prod, min_p, max_p, var_cnt, img_url = row
        item = ProductListItem(
            id=prod.id,
            name=prod.name,
            slug=prod.slug,
            component_type=prod.component_type,
            material=prod.material,
            pressure_rating=prod.pressure_rating,
            is_active=prod.is_active,
            category=prod.category,
            brand=prod.brand,
            primary_image_url=img_url,
            min_price=float(min_p) if min_p is not None else None,
            max_price=float(max_p) if max_p is not None else None,
            variant_count=var_cnt,
            created_at=prod.created_at
        )
        list_items.append(item)

    return list_items

@router.get("/{slug}", response_model=ProductDetailResponse)
async def get_product_detail(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Returns full product details along with related products.
    """
    # Fetch core product details
    stmt = (
        select(Product)
        .where(Product.slug == slug)
        .where(Product.is_active == True)
        .options(
            selectinload(Product.category),
            selectinload(Product.brand),
            selectinload(Product.variants).selectinload(ProductVariant.images),
            selectinload(Product.images),
            selectinload(Product.attributes),
        )
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Sort product variants by size or price
    product.variants = [v for v in product.variants if v.is_active]

    # Fetch related products (same category, limit 6)
    related_list = []
    if product.category_id:
        var_sub = (
            select(
                ProductVariant.product_id,
                func.min(ProductVariant.mrp).label("min_price"),
                func.max(ProductVariant.mrp).label("max_price"),
                func.count(ProductVariant.id).label("variant_count")
            )
            .where(ProductVariant.is_active == True)
            .group_by(ProductVariant.product_id)
            .subquery()
        )
        related_stmt = (
            select(
                Product,
                var_sub.c.min_price,
                var_sub.c.max_price,
                var_sub.c.variant_count,
                ProductImage.image_url.label("primary_image_url")
            )
            .join(var_sub, Product.id == var_sub.c.product_id)
            .outerjoin(
                ProductImage,
                and_(Product.id == ProductImage.product_id, ProductImage.is_primary == True)
            )
            .options(
                selectinload(Product.category),
                selectinload(Product.brand)
            )
            .where(Product.category_id == product.category_id)
            .where(Product.id != product.id)
            .where(Product.is_active == True)
            .limit(6)
        )
        related_result = await db.execute(related_stmt)
        related_rows = related_result.all()

        for r_row in related_rows:
            r_prod, r_min_p, r_max_p, r_var_cnt, r_img_url = r_row
            related_list.append(
                ProductListItem(
                    id=r_prod.id,
                    name=r_prod.name,
                    slug=r_prod.slug,
                    component_type=r_prod.component_type,
                    material=r_prod.material,
                    pressure_rating=r_prod.pressure_rating,
                    is_active=r_prod.is_active,
                    category=r_prod.category,
                    brand=r_prod.brand,
                    primary_image_url=r_img_url,
                    min_price=float(r_min_p) if r_min_p is not None else None,
                    max_price=float(r_max_p) if r_max_p is not None else None,
                    variant_count=r_var_cnt,
                    created_at=r_prod.created_at
                )
            )

    return ProductDetailResponse(
        product=ProductRead.model_validate(product),
        related_products=related_list
    )

@router.get("/{slug}/variants/{variant_id}/price", response_model=PriceBreakdown)
async def get_variant_price(
    slug: str,
    variant_id: int,
    quantity: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns calculated pricing breakdown for a specific variant & quantity.
    """
    stmt = (
        select(ProductVariant)
        .join(Product)
        .where(Product.slug == slug)
        .where(ProductVariant.id == variant_id)
        .where(ProductVariant.is_active == True)
    )
    result = await db.execute(stmt)
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )

    # Use the shared pricing service
    return calculate_price(
        variant_id=variant.id,
        quantity=quantity,
        mrp=float(variant.mrp),
        wholesale_price=float(variant.wholesale_price) if variant.wholesale_price is not None else None,
        wholesale_min_qty=variant.wholesale_min_qty
    )
