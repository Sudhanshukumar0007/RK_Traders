"""
Search services: query normalization and fuzzy matching (typo tolerance) fallback.
"""

from __future__ import annotations

import re
import logging
from typing import Any, Optional
from rapidfuzz import process

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Product, ProductVariant

logger = logging.getLogger(__name__)

# ─── Query Normalization ──────────────────────────────────────────────────────

def normalize_query(query: str) -> str:
    """
    Normalizes search query:
    1. Lowercases the query.
    2. Standardizes units (inch, inches, in -> ").
    3. Normalizes fractional numbers to their unicode symbol representation
       (e.g., 1/2, 0.5, 1 1/2, 1.5 -> ½, 1½).
    4. Removes double spaces/collapses space around units.
    """
    if not query:
        return ""

    q = query.lower().strip()

    # Normalize fractions (both spaced/hyphenated and decimals)
    # Use lookbehinds to allow word/digit characters before the fraction (e.g. 2x1 1/2 -> 2x1½)
    # while not matching letters of other words (e.g. finolex1.5 -> not replaced).
    # Use negative lookahead at the end to ensure we don't match sub-parts of other numbers
    # (e.g. 1/20 should not match 1/2).
    fraction_map = {
        # Mixed numbers / decimals
        r"(?<![a-wy-zA-WY-Z])1\s+1/2(?![0-9])": "1½", r"(?<![a-wy-zA-WY-Z])1-1/2(?![0-9])": "1½", r"(?<![a-wy-zA-WY-Z])1\.5(?![0-9])": "1½",
        r"(?<![a-wy-zA-WY-Z])2\s+1/2(?![0-9])": "2½", r"(?<![a-wy-zA-WY-Z])2-1/2(?![0-9])": "2½", r"(?<![a-wy-zA-WY-Z])2\.5(?![0-9])": "2½",
        r"(?<![a-wy-zA-WY-Z])3\s+1/2(?![0-9])": "3½", r"(?<![a-wy-zA-WY-Z])3-1/2(?![0-9])": "3½", r"(?<![a-wy-zA-WY-Z])3\.5(?![0-9])": "3½",
        r"(?<![a-wy-zA-WY-Z])4\s+1/2(?![0-9])": "4½", r"(?<![a-wy-zA-WY-Z])4-1/2(?![0-9])": "4½", r"(?<![a-wy-zA-WY-Z])4\.5(?![0-9])": "4½",

        r"(?<![a-wy-zA-WY-Z])1\s+1/4(?![0-9])": "1¼", r"(?<![a-wy-zA-WY-Z])1-1/4(?![0-9])": "1¼", r"(?<![a-wy-zA-WY-Z])1\.25(?![0-9])": "1¼",
        r"(?<![a-wy-zA-WY-Z])2\s+1/4(?![0-9])": "2¼", r"(?<![a-wy-zA-WY-Z])2-1/4(?![0-9])": "2¼", r"(?<![a-wy-zA-WY-Z])2\.25(?![0-9])": "2¼",

        r"(?<![a-wy-zA-WY-Z])1\s+3/4(?![0-9])": "1¾", r"(?<![a-wy-zA-WY-Z])1-3/4(?![0-9])": "1¾", r"(?<![a-wy-zA-WY-Z])1\.75(?![0-9])": "1¾",
        r"(?<![a-wy-zA-WY-Z])2\s+3/4(?![0-9])": "2¾", r"(?<![a-wy-zA-WY-Z])2-3/4(?![0-9])": "2¾", r"(?<![a-wy-zA-WY-Z])2\.75(?![0-9])": "2¾",

        # Standalone fractions / decimals
        r"(?<![a-wy-zA-WY-Z])1/2(?![0-9])": "½", r"(?<![a-wy-zA-WY-Z])0\.5(?![0-9])": "½",
        r"(?<![a-wy-zA-WY-Z])1/4(?![0-9])": "¼", r"(?<![a-wy-zA-WY-Z])0\.25(?![0-9])": "¼",
        r"(?<![a-wy-zA-WY-Z])3/4(?![0-9])": "¾", r"(?<![a-wy-zA-WY-Z])0\.75(?![0-9])": "¾",
    }

    for pattern, replacement in fraction_map.items():
        q = re.sub(pattern, replacement, q)

    # Normalize units
    # "inch", "inches", "in" (with word boundary) -> "
    # Note: we don't want to replace "in" inside words like "fitting" or "finolex"
    q = re.sub(r"(?<![a-zA-Z])(inches|inch|in)\b", '"', q)

    # Collapse space before double quotes (e.g. '1/2 "' -> '½"')
    q = re.sub(r'\s+"', '"', q)

    # Collapse multiple spaces
    q = re.sub(r"\s+", " ", q).strip()

    return q


# ─── Fuzzy Matcher ────────────────────────────────────────────────────────────

class FuzzyMatcher:
    """
    In-memory cache of products and variant names/attributes for fast,
    typo-tolerant search fallback using RapidFuzz.
    """
    _instance: Optional[FuzzyMatcher] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.documents: list[dict[str, Any]] = []
        self._initialized = True

    async def initialize(self, db: AsyncSession) -> None:
        """
        Loads catalog items from the database into the cache.
        """
        logger.info("Initializing FuzzyMatcher cache...")
        try:
            # Query active products and load variants & category
            stmt = (
                select(Product)
                .where(Product.is_active == True)
                .options(
                    selectinload(Product.variants),
                    selectinload(Product.category),
                    selectinload(Product.brand),
                )
            )
            result = await db.execute(stmt)
            products = result.scalars().all()

            docs = []
            for p in products:
                # 1. Product-level document
                product_text = f"{p.name} {p.component_type or ''} {p.material or ''} {p.pressure_rating or ''}"
                if p.category:
                    product_text += f" {p.category.name}"
                if p.brand:
                    product_text += f" {p.brand.name}"

                docs.append({
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "text": normalize_query(product_text),
                    "type": "product"
                })

                # 2. Variant-level documents
                for v in p.variants:
                    if not v.is_active:
                        continue
                    variant_text = f"{p.name} {v.size_label or ''} {v.sku}"
                    if p.component_type:
                        variant_text += f" {p.component_type}"
                    if p.pressure_rating:
                        variant_text += f" {p.pressure_rating}"

                    docs.append({
                        "id": p.id,  # return the product ID
                        "name": p.name,
                        "slug": p.slug,
                        "text": normalize_query(variant_text),
                        "type": "variant",
                        "sku": v.sku,
                        "size_label": v.size_label
                    })

            self.documents = docs
            logger.info(f"FuzzyMatcher initialized with {len(self.documents)} documents.")
        except Exception as e:
            logger.error(f"Failed to initialize FuzzyMatcher: {e}")

    def search(self, query: str, limit: int = 10, threshold: float = 50.0) -> list[dict[str, Any]]:
        """
        Performs in-memory fuzzy search using RapidFuzz against cached documents.
        """
        if not self.documents:
            return []

        norm_query = normalize_query(query)
        choices = [doc["text"] for doc in self.documents]

        # Extract matches
        matches = process.extract(
            norm_query,
            choices,
            limit=limit * 2,  # get extra to de-duplicate product IDs
            score_cutoff=threshold
        )

        seen_product_ids = set()
        results = []

        for match_text, score, index in matches:
            doc = self.documents[index]
            product_id = doc["id"]
            if product_id not in seen_product_ids:
                seen_product_ids.add(product_id)
                results.append({
                    "id": product_id,
                    "name": doc["name"],
                    "slug": doc["slug"],
                    "score": score
                })
                if len(results) >= limit:
                    break

        return results


# Global singleton instance
fuzzy_matcher = FuzzyMatcher()
