"""
Shipping service: volumetric weight calculation + Shiprocket API wrapper
with a mock fallback when no credentials are provided.
"""

from __future__ import annotations

import os
import logging
import time
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

SHIPROCKET_EMAIL = os.getenv("SHIPROCKET_EMAIL", "")
SHIPROCKET_PASSWORD = os.getenv("SHIPROCKET_PASSWORD", "")
SHIPROCKET_API_BASE = "https://apiv2.shiprocket.in/v1/external"

# Mock mode when no credentials
USE_MOCK = not (SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD)


# ─── Volumetric weight ────────────────────────────────────────────────────────

def billable_weight_kg(items: list[dict]) -> float:
    """
    Calculate the billable weight for a list of order items.

    Each item dict should have:
        - weight_grams: int
        - dimensions_cm: {length, width, height}
        - quantity: int

    Billable weight = max(actual_weight_kg, volumetric_weight_kg)
    Volumetric divisor: 5000 (standard for most Indian couriers)
    """
    total_actual_grams = 0
    total_volumetric_cc = 0

    for item in items:
        qty = item.get("quantity", 1)
        weight_g = item.get("weight_grams") or 200  # 200g fallback

        dims = item.get("dimensions_cm") or {}
        l = dims.get("length", 10)
        w = dims.get("width", 10)
        h = dims.get("height", 5)

        total_actual_grams += weight_g * qty
        total_volumetric_cc += l * w * h * qty

    actual_kg = total_actual_grams / 1000
    volumetric_kg = total_volumetric_cc / 5000

    billable = max(actual_kg, volumetric_kg)
    return round(max(billable, 0.5), 2)  # minimum 0.5 kg


# ─── Shiprocket auth token (with in-memory cache) ────────────────────────────

_cached_token: Optional[str] = None
_token_expiry: float = 0.0
TOKEN_TTL_SECONDS = 24 * 3600  # Shiprocket tokens are valid for 24h


async def get_shiprocket_token() -> str:
    global _cached_token, _token_expiry
    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{SHIPROCKET_API_BASE}/auth/login",
            json={"email": SHIPROCKET_EMAIL, "password": SHIPROCKET_PASSWORD},
        )
        resp.raise_for_status()
        data = resp.json()
        _cached_token = data["token"]
        _token_expiry = time.time() + TOKEN_TTL_SECONDS - 300  # refresh 5 min early
        return _cached_token


# ─── Shipping quote ───────────────────────────────────────────────────────────

MOCK_QUOTES = [
    {
        "courier_name": "Delhivery",
        "service_name": "Surface",
        "rate": 80,
        "estimated_days": "3–5 business days",
    },
    {
        "courier_name": "BlueDart",
        "service_name": "Priority",
        "rate": 150,
        "estimated_days": "1–2 business days",
    },
    {
        "courier_name": "DTDC",
        "service_name": "Standard",
        "rate": 100,
        "estimated_days": "4–6 business days",
    },
]


async def get_shipping_quotes(
    pincode: str,
    weight_kg: float,
    cod: bool = False,
) -> list[dict]:
    """Return available courier options with cost estimates."""
    if USE_MOCK:
        logger.info("Shipping: using mock quotes (no Shiprocket credentials)")
        # Adjust mock rates by weight
        adjusted = []
        for q in MOCK_QUOTES:
            rate = q["rate"] + max(0, (weight_kg - 0.5)) * 40  # ₹40 per extra 0.5 kg
            adjusted.append({**q, "rate": round(rate)})
        return adjusted

    try:
        token = await get_shiprocket_token()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{SHIPROCKET_API_BASE}/courier/serviceability/",
                params={
                    "pickup_postcode": "400001",  # your warehouse pincode
                    "delivery_postcode": pincode,
                    "weight": weight_kg,
                    "cod": 1 if cod else 0,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            couriers = data.get("data", {}).get("available_courier_companies", [])

            return [
                {
                    "courier_name": c.get("courier_name", ""),
                    "service_name": c.get("courier_name", ""),
                    "rate": c.get("rate", 100),
                    "estimated_days": f"{c.get('etd', 'N/A')} days",
                }
                for c in couriers[:5]  # top 5
            ]
    except Exception as exc:
        logger.warning("Shiprocket serviceability check failed: %s — falling back to mock", exc)
        return MOCK_QUOTES


# ─── Create shipment ──────────────────────────────────────────────────────────

async def create_shipment(order_data: dict) -> dict:
    """
    Push order to Shiprocket and get AWB code.
    Returns: {awb_code, courier_name, label_url}
    """
    if USE_MOCK:
        import random
        import string
        fake_awb = "AWB" + "".join(random.choices(string.digits, k=9))
        logger.info("Shipping mock: generated AWB %s", fake_awb)
        return {
            "awb_code": fake_awb,
            "courier_name": "Delhivery (Mock)",
            "label_url": None,
            "shipment_id": None,
        }

    token = await get_shiprocket_token()
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Create order in Shiprocket
        resp = await client.post(
            f"{SHIPROCKET_API_BASE}/orders/create/adhoc",
            json=order_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        order_resp = resp.json()
        shipment_id = order_resp.get("shipment_id")

        # 2. Assign courier
        assign_resp = await client.post(
            f"{SHIPROCKET_API_BASE}/courier/assign/awb",
            json={"shipment_id": shipment_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assign_resp.raise_for_status()
        awb_data = assign_resp.json().get("response", {}).get("data", {})

        return {
            "awb_code": awb_data.get("awb_code"),
            "courier_name": awb_data.get("courier_name"),
            "label_url": awb_data.get("label_url"),
            "shipment_id": shipment_id,
        }


# ─── Tracking ─────────────────────────────────────────────────────────────────

MOCK_TRACKING = {
    "current_status": "In Transit",
    "tracking_history": [
        {"date": "2026-06-20", "activity": "Order created", "location": "Mumbai"},
        {"date": "2026-06-21", "activity": "Picked up", "location": "Mumbai Hub"},
        {"date": "2026-06-22", "activity": "In transit", "location": "Pune Sorting Center"},
    ],
}


async def get_tracking_info(awb_code: str) -> dict:
    if USE_MOCK:
        return MOCK_TRACKING

    token = await get_shiprocket_token()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{SHIPROCKET_API_BASE}/courier/track/awb/{awb_code}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        data = resp.json()
        tracking = data.get("tracking_data", {})
        return {
            "current_status": tracking.get("shipment_status", "Unknown"),
            "tracking_history": [
                {
                    "date": e.get("date"),
                    "activity": e.get("activity"),
                    "location": e.get("location"),
                }
                for e in tracking.get("shipment_track_activities", [])
            ],
        }
