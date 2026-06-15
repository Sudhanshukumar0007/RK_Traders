from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown: close DB connections
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack e-commerce API for hardware & plumbing supplies",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving (uploaded product images) ────────────────────────────
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router)

# Phase 2+ routers will be added here:
# app.include_router(products.router, prefix=settings.API_V1_STR)
# app.include_router(categories.router, prefix=settings.API_V1_STR)
# app.include_router(search.router, prefix=settings.API_V1_STR)
# app.include_router(auth.router, prefix=settings.API_V1_STR)
# app.include_router(cart.router, prefix=settings.API_V1_STR)
# app.include_router(orders.router, prefix=settings.API_V1_STR)
# app.include_router(shipping.router, prefix=settings.API_V1_STR)
