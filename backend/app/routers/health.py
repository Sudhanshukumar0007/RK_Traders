from fastapi import APIRouter
from app.core.database import check_db_connection

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns 200 if the API is up and DB is reachable.
    """
    db_ok = await check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "api": "ok",
        "db": "connected" if db_ok else "unreachable",
    }
