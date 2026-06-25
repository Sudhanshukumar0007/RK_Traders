"""
Search router — endpoints for searching the catalog.
Uses Postgres full-text search first, with a fallback to FuzzyMatcher (RapidFuzz).
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.models.catalog import Product, ProductVariant, ProductImage
from app.schemas.catalog import ProductListItem
from app.services.search import normalize_query, fuzzy_matcher

router = APIRouter(prefix="/search", tags=["search"])

class SearchResponse(BaseModel):
    results: list[ProductListItem]
    fuzzy_fallback_used: bool
    query: str

@router.get("", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_catalog(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search product catalog using PostgreSQL Full-Text Search.
    Falls back to RapidFuzz fuzzy matcher in-memory cache if fewer than 3 results are found.
    Rate limited to 30 requests per minute per IP.
    """
    normalized_q = normalize_query(q)
    if not normalized_q:
        return SearchResponse(results=[], fuzzy_fallback_used=False, query=q)

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

    # Base select query helper for product list item attributes
    def get_products_select_stmt():
        return (
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
            .where(Product.is_active == True)
        )

    # 1. Try PostgreSQL Full-Text Search (FTS)
    # Using plainto_tsquery or websearch_to_tsquery
    # Split query by spaces to make it search-friendly for websearch_to_tsquery
    fts_stmt = (
        get_products_select_stmt()
        .where(Product.search_vector.op("@@")(func.websearch_to_tsquery("english", normalized_q)))
        .limit(limit)
    )

    result = await db.execute(fts_stmt)
    rows = result.all()

    results_list = []
    fuzzy_fallback_used = False

    # Helper to map database row to ProductListItem schema
    def map_row_to_schema(row):
        prod, min_p, max_p, var_cnt, img_url = row
        return ProductListItem(
            id=prod.id,
            name=prod.name,
            slug=prod.slug,
            component_type=prod.component_type,
            material=prod.material,
            pressure_rating=prod.pressure_rating,
            is_active=prod.is_active,
            category=None,  # list view doesn't strictly require category tree nested
            brand=None,
            primary_image_url=img_url,
            min_price=float(min_p) if min_p is not None else None,
            max_price=float(max_p) if max_p is not None else None,
            variant_count=var_cnt,
            created_at=prod.created_at
        )

    for row in rows:
        results_list.append(map_row_to_schema(row))

    # 2. Trigger Fuzzy Fallback if 0 results
    if len(results_list) == 0:
        if not fuzzy_matcher.documents:
            await fuzzy_matcher.initialize(db)
        fuzzy_matches = fuzzy_matcher.search(q, limit=limit)
        
        if fuzzy_matches:
            # Gather product IDs from fuzzy matches
            fuzzy_product_ids = [m["id"] for m in fuzzy_matches]
            
            # Query the database for these specific products
            fuzzy_stmt = (
                get_products_select_stmt()
                .where(Product.id.in_(fuzzy_product_ids))
            )
            
            fuzzy_result = await db.execute(fuzzy_stmt)
            fuzzy_rows = fuzzy_result.all()
            
            # Map database rows to schemas
            fuzzy_map = {row[0].id: map_row_to_schema(row) for row in fuzzy_rows}
            
            # Re-sort products based on fuzzy match score order
            fallback_results = []
            for match in fuzzy_matches:
                pid = match["id"]
                if pid in fuzzy_map:
                    fallback_results.append(fuzzy_map[pid])
            
            results_list = fallback_results
            fuzzy_fallback_used = True

    return SearchResponse(
        results=results_list,
        fuzzy_fallback_used=fuzzy_fallback_used,
        query=q
    )
