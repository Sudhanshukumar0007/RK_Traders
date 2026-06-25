"""
Categories router — endpoints for managing and retrieving categories.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.catalog import Category
from app.schemas.catalog import CategoryTree

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("", response_model=list[CategoryTree])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    Returns the hierarchical category tree (root categories with nested children).
    """
    stmt = (
        select(Category)
        .where(Category.parent_id == None)
        .where(Category.is_active == True)
        .options(selectinload(Category.children))
        .order_by(Category.name)
    )
    result = await db.execute(stmt)
    roots = result.scalars().all()
    
    # Note: selectinload eagerly loads category.children.
    # If a child category is inactive, we should ideally filter it out.
    # Let's filter out inactive children in python to be safe and clean.
    tree = []
    for root in roots:
        # Construct the nested structure manually to avoid triggering lazy-load on child.children
        children_data = []
        for child in root.children:
            if child.is_active:
                children_data.append(
                    CategoryTree(
                        id=child.id,
                        name=child.name,
                        slug=child.slug,
                        parent_id=child.parent_id,
                        image_url=child.image_url,
                        description=child.description,
                        is_active=child.is_active,
                        created_at=child.created_at,
                        children=[]  # limit depth to 2 levels (root -> child)
                    )
                )
        
        root_node = CategoryTree(
            id=root.id,
            name=root.name,
            slug=root.slug,
            parent_id=root.parent_id,
            image_url=root.image_url,
            description=root.description,
            is_active=root.is_active,
            created_at=root.created_at,
            children=children_data
        )
        tree.append(root_node)
        
    return tree
