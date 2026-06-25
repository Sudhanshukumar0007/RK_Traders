"""
Seed script — inserts ~20 sample UPVC plumbing products with realistic data.
Run from the backend directory:
    python -m app.seed

Uses an asyncio event loop with the async engine.
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


# ─── Seed data ────────────────────────────────────────────────────────────────

BRANDS = [
    {"name": "Supreme", "slug": "supreme", "logo_url": None},
    {"name": "Finolex", "slug": "finolex", "logo_url": None},
    {"name": "Astral", "slug": "astral", "logo_url": None},
]

CATEGORIES = [
    # Top-level
    {"name": "Plumbing", "slug": "plumbing", "parent_slug": None},
    # Sub-categories of Plumbing
    {"name": "UPVC Fittings", "slug": "upvc-fittings", "parent_slug": "plumbing"},
    {"name": "UPVC Pipes", "slug": "upvc-pipes", "parent_slug": "plumbing"},
    {"name": "CPVC Fittings", "slug": "cpvc-fittings", "parent_slug": "plumbing"},
    {"name": "GI Fittings", "slug": "gi-fittings", "parent_slug": "plumbing"},
    {"name": "SCH 80 Fittings", "slug": "sch-80-fittings", "parent_slug": "plumbing"},
    {"name": "Brass Fittings", "slug": "brass-fittings", "parent_slug": "plumbing"},
]

# Products with their variants
# Fields: name, slug, category_slug, brand_slug, component_type, material, pressure_rating, description, variants
PRODUCTS = [

    {

        "name": "Coupler SCH 80",

        "slug": "coupler-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Coupler",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Coupler SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "COUPLER-SCH-80-1-2",

                "mrp": 9.5,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "COUPLER-SCH-80-1",

                "mrp": 22.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 32",

        "slug": "1-4-32",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 32",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 32 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 42",

        "slug": "1-2-42",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 42",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 42 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-42-2",

                "mrp": 61.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-42-3",

                "mrp": 184.0,

                "stock": 100

            }

        ],

        "image": "coupler_sch80.png"

    },

    {

        "name": "Elbow 90* SCH 80",

        "slug": "elbow-90-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Elbow 90*",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Elbow 90* SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "ELBOW-90-SCH-80-1-2",

                "mrp": 14.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "ELBOW-90-SCH-80-1",

                "mrp": 32.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 50",

        "slug": "1-4-50",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 50",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 50 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 67",

        "slug": "1-2-67",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 67",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 67 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-67-2",

                "mrp": 100.5,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-67-3",

                "mrp": 304.0,

                "stock": 100

            }

        ],

        "image": "elbow_sch_80.png"

    },

    {

        "name": "Tee SCH 80",

        "slug": "tee-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Tee",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Tee SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "TEE-SCH-80-1-2",

                "mrp": 17.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "TEE-SCH-80-1",

                "mrp": 44.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 66.5",

        "slug": "1-4-66-5",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 66.5",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 66.5 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 89",

        "slug": "1-2-89",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 89",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 89 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-89-2",

                "mrp": 143.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-89-3",

                "mrp": 413.5,

                "stock": 100

            }

        ],

        "image": "tee_sch80.png"

    },

    {

        "name": "Cross SCH 80",

        "slug": "cross-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Cross",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Cross SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "CROSS-SCH-80-1-2",

                "mrp": 22.5,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "CROSS-SCH-80-1",

                "mrp": 44.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 171",

        "slug": "1-4-171",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 171",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 171 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 231",

        "slug": "1-2-231",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 231",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 231 for plumbing applications.",

        "variants": [],

        "image": "Cross_SCH_80.png"

    },

    {

        "name": "Elbow 45* SCH 80",

        "slug": "elbow-45-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Elbow 45*",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Elbow 45* SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "ELBOW-45-SCH-80-1-2",

                "mrp": 11.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "ELBOW-45-SCH-80-1",

                "mrp": 27.5,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 42",

        "slug": "1-4-42",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 42",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 42 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 57",

        "slug": "1-2-57",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 57",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 57 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-57-2",

                "mrp": 87.5,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-57-3",

                "mrp": 250.0,

                "stock": 100

            }

        ],

        "image": "elbow_45degree_sch40.png"

    },

    {

        "name": "Union SCH 80",

        "slug": "union-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Union",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Union SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "UNION-SCH-80-1-2",

                "mrp": 34.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "UNION-SCH-80-1",

                "mrp": 63.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 97",

        "slug": "1-4-97",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 97",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 97 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 143",

        "slug": "1-2-143",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 143",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 143 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-143-2",

                "mrp": 184.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-143-3",

                "mrp": 614.0,

                "stock": 100

            }

        ],

        "image": "unicorn_sch80.png"

    },

    {

        "name": "Ball Valve SCH 80",

        "slug": "ball-valve-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Ball Valve",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Ball Valve SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "BALL-VALVE-SCH-80-1-2",

                "mrp": 83.5,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "BALL-VALVE-SCH-80-1",

                "mrp": 194.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 294",

        "slug": "1-4-294",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 294",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 294 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 349",

        "slug": "1-2-349",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 349",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 349 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-349-2",

                "mrp": 534.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-349-3",

                "mrp": 2267.0,

                "stock": 100

            }

        ],

        "image": "ball_valve_sch_80.png"

    },

    {

        "name": "Tank Connector SCH 80",

        "slug": "tank-connector-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Tank Connector",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Tank Connector SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "TANK-CONNECTOR-SCH-80-1-2",

                "mrp": 29.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "TANK-CONNECTOR-SCH-80-1",

                "mrp": 60.5,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 67",

        "slug": "1-4-67",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 67",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 67 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 76",

        "slug": "1-2-76",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 76",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 76 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-76-2",

                "mrp": 103.5,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-76-3",

                "mrp": 292.5,

                "stock": 100

            }

        ],

        "image": "tank_connector_sch80.png"

    },

    {

        "name": "MTA Plastic SCH 80",

        "slug": "mta-plastic-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "MTA Plastic",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality MTA Plastic SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "MTA-PLASTIC-SCH-80-1-2",

                "mrp": 7.5,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "MTA-PLASTIC-SCH-80-1",

                "mrp": 17.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 30",

        "slug": "1-4-30",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 30",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 30 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 34",

        "slug": "1-2-34",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 34",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 34 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-34-2",

                "mrp": 50.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-34-3",

                "mrp": 144.0,

                "stock": 100

            }

        ],

        "image": "mta_plastic_sch80.png"

    },

    {

        "name": "FTA Plastic SCH 80",

        "slug": "fta-plastic-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "FTA Plastic",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality FTA Plastic SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "FTA-PLASTIC-SCH-80-1-2",

                "mrp": 9.5,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "FTA-PLASTIC-SCH-80-1",

                "mrp": 21.5,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 30",

        "slug": "1-4-30",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 30",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 30 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 35.5",

        "slug": "1-2-35-5",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 35.5",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 35.5 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-35-5-2",

                "mrp": 60.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-35-5-3",

                "mrp": 151.5,

                "stock": 100

            }

        ],

        "image": "fta_plastic_sch80.png"

    },

    {

        "name": "Reducer SCH 80",

        "slug": "reducer-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Reducer",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Reducer SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1\" x 1/2\"",

                "sku": "REDUCER-SCH-80-1-X-1-2",

                "mrp": 22.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\" x 1\": 31",

        "slug": "1-4-x-1-31",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\" x 1\": 31",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\" x 1\": 31 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\" x 1\": 47",

        "slug": "1-2-x-1-47",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\" x 1\": 47",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\" x 1\": 47 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\" x 1\"",

                "sku": "1-2-X-1-47-2-X-1",

                "mrp": 60.5,

                "stock": 100

            },

            {

                "size_label": "2\" x 1.1/2\"",

                "sku": "1-2-X-1-47-2-X-1-1-2",

                "mrp": 73.5,

                "stock": 100

            },

            {

                "size_label": "3\" x 2\"",

                "sku": "1-2-X-1-47-3-X-2",

                "mrp": 153.0,

                "stock": 100

            }

        ],

        "image": "reducer_sch_80.png"

    },

    {

        "name": "Reducer Bush SCH 80",

        "slug": "reducer-bush-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Reducer Bush",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Reducer Bush SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1\" x 1/2\"",

                "sku": "REDUCER-BUSH-SCH-80-1-X-1-2",

                "mrp": 11.5,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\" x 1\": 13",

        "slug": "1-4-x-1-13",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\" x 1\": 13",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\" x 1\": 13 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\" x 1/2\": 26",

        "slug": "1-2-x-1-2-26",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\" x 1/2\": 26",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\" x 1/2\": 26 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\" x 1\": 24.5",

        "slug": "1-2-x-1-24-5",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\" x 1\": 24.5",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\" x 1\": 24.5 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\" x 1.1/4\": 13",

        "slug": "1-2-x-1-1-4-13",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\" x 1.1/4\": 13",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\" x 1.1/4\": 13 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\" x 1\"",

                "sku": "1-2-X-1-1-4-13-2-X-1",

                "mrp": 38.0,

                "stock": 100

            },

            {

                "size_label": "2\" x 1.1/2\"",

                "sku": "1-2-X-1-1-4-13-2-X-1-1-2",

                "mrp": 31.0,

                "stock": 100

            },

            {

                "size_label": "3\" x 2\"",

                "sku": "1-2-X-1-1-4-13-3-X-2",

                "mrp": 163.0,

                "stock": 100

            }

        ],

        "image": "reducer_bush_sch80.png"

    },

    {

        "name": "Reducer Tee SCH 80",

        "slug": "reducer-tee-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Reducer Tee",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Reducer Tee SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1\" x 1/2\"",

                "sku": "REDUCER-TEE-SCH-80-1-X-1-2",

                "mrp": 37.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\" x 1\": 68",

        "slug": "1-4-x-1-68",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\" x 1\": 68",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\" x 1\": 68 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\" x 1\": 74",

        "slug": "1-2-x-1-74",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\" x 1\": 74",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\" x 1\": 74 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\" x 1\"",

                "sku": "1-2-X-1-74-2-X-1",

                "mrp": 133.0,

                "stock": 100

            },

            {

                "size_label": "3\" x 2\"",

                "sku": "1-2-X-1-74-3-X-2",

                "mrp": 375.0,

                "stock": 100

            }

        ],

        "image": "reducer_tee_sch80.png"

    },

    {

        "name": "Reducer Elbow SCH 80",

        "slug": "reducer-elbow-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Reducer Elbow",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Reducer Elbow SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1\" x 1/2\"",

                "sku": "REDUCER-ELBOW-SCH-80-1-X-1-2",

                "mrp": 30.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\" x 1\": 80",

        "slug": "1-4-x-1-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\" x 1\": 80",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\" x 1\": 80 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\" x 1\": 88",

        "slug": "1-2-x-1-88",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\" x 1\": 88",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\" x 1\": 88 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\" x 1\"",

                "sku": "1-2-X-1-88-2-X-1",

                "mrp": 265.0,

                "stock": 100

            }

        ],

        "image": "reducer_elbow_sch80.png"

    },

    {

        "name": "End Cap SCH 80",

        "slug": "end-cap-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "End Cap",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality End Cap SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "END-CAP-SCH-80-1-2",

                "mrp": 6.5,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "END-CAP-SCH-80-1",

                "mrp": 15.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 23",

        "slug": "1-4-23",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 23",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 23 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 32",

        "slug": "1-2-32",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 32",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 32 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-32-2",

                "mrp": 46.5,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-32-3",

                "mrp": 129.5,

                "stock": 100

            }

        ],

        "image": "endcap_sch80.png"

    },

    {

        "name": "Bypass Bend SCH 80",

        "slug": "bypass-bend-sch-80",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "Bypass Bend",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality Bypass Bend SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "BYPASS-BEND-SCH-80-1-2",

                "mrp": 52.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "BYPASS-BEND-SCH-80-1",

                "mrp": 117.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 143",

        "slug": "1-4-143",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 143",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 143 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 194",

        "slug": "1-2-194",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 194",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 194 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-194-2",

                "mrp": 392.0,

                "stock": 100

            }

        ],

        "image": "bypass_bend_sch_80.png"

    },

    {

        "name": "Brass Elbow SCH 80",

        "slug": "brass-elbow-sch-80",

        "category_slug": "brass-fittings",

        "brand_slug": "supreme",

        "component_type": "Brass Elbow",

        "material": "Brass",

        "pressure_rating": "SCH-80",

        "description": "High quality Brass Elbow SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "BRASS-ELBOW-SCH-80-1-2",

                "mrp": 98.0,

                "stock": 100

            },

            {

                "size_label": "3/4\"",

                "sku": "BRASS-ELBOW-SCH-80-3-4",

                "mrp": 151.5,

                "stock": 100

            },

            {

                "size_label": "1\" x 1/2\"",

                "sku": "BRASS-ELBOW-SCH-80-1-X-1-2",

                "mrp": 141.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "BRASS-ELBOW-SCH-80-1",

                "mrp": 319.0,

                "stock": 100

            }

        ],

        "image": "brass_elbow_sch_80.png"

    },

    {

        "name": "Brass Tee SCH 80",

        "slug": "brass-tee-sch-80",

        "category_slug": "brass-fittings",

        "brand_slug": "supreme",

        "component_type": "Brass Tee",

        "material": "Brass",

        "pressure_rating": "SCH-80",

        "description": "High quality Brass Tee SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "BRASS-TEE-SCH-80-1-2",

                "mrp": 115.0,

                "stock": 100

            },

            {

                "size_label": "3/4\"",

                "sku": "BRASS-TEE-SCH-80-3-4",

                "mrp": 157.0,

                "stock": 100

            },

            {

                "size_label": "1\" x 1/2\"",

                "sku": "BRASS-TEE-SCH-80-1-X-1-2",

                "mrp": 153.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "BRASS-TEE-SCH-80-1",

                "mrp": 212.0,

                "stock": 100

            }

        ],

        "image": "brass_tee_sch80.png"

    },

    {

        "name": "Brass MTA SCH 80",

        "slug": "brass-mta-sch-80",

        "category_slug": "brass-fittings",

        "brand_slug": "supreme",

        "component_type": "Brass MTA",

        "material": "Brass",

        "pressure_rating": "SCH-80",

        "description": "High quality Brass MTA SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "BRASS-MTA-SCH-80-1-2",

                "mrp": 131.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "BRASS-MTA-SCH-80-1",

                "mrp": 234.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 422",

        "slug": "1-4-422",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 422",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 422 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 519.5",

        "slug": "1-2-519-5",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 519.5",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 519.5 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-519-5-2",

                "mrp": 722.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-519-5-3",

                "mrp": 1792.0,

                "stock": 100

            },

            {

                "size_label": "1\" x 1/2\"",

                "sku": "1-2-519-5-1-X-1-2",

                "mrp": 162.0,

                "stock": 100

            }

        ],

        "image": "brass_mta_sch80.png"

    },

    {

        "name": "Brass FTA SCH 80",

        "slug": "brass-fta-sch-80",

        "category_slug": "brass-fittings",

        "brand_slug": "supreme",

        "component_type": "Brass FTA",

        "material": "Brass",

        "pressure_rating": "SCH-80",

        "description": "High quality Brass FTA SCH 80 for plumbing applications.",

        "variants": [

            {

                "size_label": "1/2\"",

                "sku": "BRASS-FTA-SCH-80-1-2",

                "mrp": 88.0,

                "stock": 100

            },

            {

                "size_label": "1\"",

                "sku": "BRASS-FTA-SCH-80-1",

                "mrp": 244.0,

                "stock": 100

            }

        ]

    },

    {

        "name": "1/4\": 323.5",

        "slug": "1-4-323-5",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/4\": 323.5",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/4\": 323.5 for plumbing applications.",

        "variants": []

    },

    {

        "name": "1/2\": 400",

        "slug": "1-2-400",

        "category_slug": "sch-80-fittings",

        "brand_slug": "supreme",

        "component_type": "1/2\": 400",

        "material": "UPVC",

        "pressure_rating": "SCH-80",

        "description": "High quality 1/2\": 400 for plumbing applications.",

        "variants": [

            {

                "size_label": "2\"",

                "sku": "1-2-400-2",

                "mrp": 691.0,

                "stock": 100

            },

            {

                "size_label": "3\"",

                "sku": "1-2-400-3",

                "mrp": 1646.0,

                "stock": 100

            },

            {

                "size_label": "1\" x 1/2\"",

                "sku": "1-2-400-1-X-1-2",

                "mrp": 116.0,

                "stock": 100

            }

        ],

        "image": "brass_fta_sch80.png"

    }

]




# ─── Seed runner ──────────────────────────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    print("Seeding database...")

    # ── Brands ──
    brand_id_map: dict[str, int] = {}
    for b in BRANDS:
        result = await db.execute(
            text("INSERT INTO brands (name, slug, is_active) VALUES (:name, :slug, TRUE) ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id"),
            {"name": b["name"], "slug": b["slug"]},
        )
        brand_id_map[b["slug"]] = result.scalar_one()
    await db.commit()
    print(f"  [OK] {len(BRANDS)} brands seeded")

    # ── Categories ──
    category_id_map: dict[str, int] = {}

    # Insert top-level first
    top_level = [c for c in CATEGORIES if c["parent_slug"] is None]
    for c in top_level:
        result = await db.execute(
            text("INSERT INTO categories (name, slug, parent_id, is_active) VALUES (:name, :slug, NULL, TRUE) ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id"),
            {"name": c["name"], "slug": c["slug"]},
        )
        category_id_map[c["slug"]] = result.scalar_one()
    await db.commit()

    # Insert sub-categories
    sub_level = [c for c in CATEGORIES if c["parent_slug"] is not None]
    for c in sub_level:
        parent_id = category_id_map.get(c["parent_slug"])
        result = await db.execute(
            text("INSERT INTO categories (name, slug, parent_id, is_active) VALUES (:name, :slug, :parent_id, TRUE) ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id"),
            {"name": c["name"], "slug": c["slug"], "parent_id": parent_id},
        )
        category_id_map[c["slug"]] = result.scalar_one()
    await db.commit()
    print(f"  [OK] {len(CATEGORIES)} categories seeded")

    # ── Products + Variants ──
    product_count = 0
    variant_count = 0

    for p in PRODUCTS:
        cat_id = category_id_map.get(p["category_slug"])
        brand_id = brand_id_map.get(p["brand_slug"])

        result = await db.execute(
            text("""
                INSERT INTO products (name, slug, description, category_id, brand_id, component_type, material, pressure_rating, is_active)
                VALUES (:name, :slug, :desc, :cat_id, :brand_id, :comp_type, :material, :pressure, TRUE)
                ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """),
            {
                "name": p["name"],
                "slug": p["slug"],
                "desc": p["description"],
                "cat_id": cat_id,
                "brand_id": brand_id,
                "comp_type": p["component_type"],
                "material": p["material"],
                "pressure": p["pressure_rating"],
            },
        )
        product_id = result.scalar_one()
        product_count += 1

        # Attributes
        for attr in p.get("attributes", []):
            await db.execute(
                text("""
                    INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
                    VALUES (:pid, :aname, :aval)
                    ON CONFLICT DO NOTHING
                """),
                {"pid": product_id, "aname": attr["name"], "aval": attr["value"]},
            )

        # Image
        if p.get("image"):
            await db.execute(
                text("""
                    INSERT INTO product_images (product_id, image_url, is_primary, display_order)
                    VALUES (:pid, :img, TRUE, 0)
                """),
                {"pid": product_id, "img": p["image"]},
            )

        # Variants
        for v in p.get("variants", []):
            dim = v.get("dim", {"length": 5, "width": 5, "height": 5})
            await db.execute(
                text("""
                    INSERT INTO product_variants
                        (product_id, sku, size_label, mrp, wholesale_price, wholesale_min_qty, stock_quantity, reserved_quantity, low_stock_threshold, weight_grams, dimensions_cm, is_active)
                    VALUES
                        (:pid, :sku, :size_label, :mrp, :wp, :wq, :stock, 0, 10, :weight, CAST(:dims AS jsonb), TRUE)
                    ON CONFLICT (sku) DO UPDATE SET
                        stock_quantity = EXCLUDED.stock_quantity,
                        mrp = EXCLUDED.mrp
                """),
                {
                    "pid": product_id,
                    "sku": v["sku"],
                    "size_label": v["size_label"],
                    "mrp": v["mrp"],
                    "wp": v.get("wholesale_price"),
                    "wq": v.get("wholesale_min_qty"),
                    "stock": v.get("stock", 100),
                    "weight": v.get("weight_g"),
                    "dims": str(dim).replace("'", '"'),
                },
            )
            variant_count += 1

    await db.commit()
    print(f"  [OK] {product_count} products seeded")
    print(f"  [OK] {variant_count} variants seeded")

    # ── Full-text search vector update ──
    await db.execute(text("""
        UPDATE products
        SET search_vector = to_tsvector('english',
            coalesce(name, '') || ' ' ||
            coalesce(description, '') || ' ' ||
            coalesce(component_type, '') || ' ' ||
            coalesce(material, '') || ' ' ||
            coalesce(pressure_rating, '')
        )
    """))
    await db.commit()
    print("  [OK] Full-text search vectors updated")

    print("\nSeed complete!")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
