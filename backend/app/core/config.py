import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://supreme:supreme@localhost:5432/supreme_hardware"
    DATABASE_URL_SYNC: str = "postgresql+pg8000://supreme:supreme@localhost:5432/supreme_hardware"

    # JWT
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    PROJECT_NAME: str = "Supreme Hardware Store"
    API_V1_STR: str = "/api"
    DEBUG: bool = False

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # File storage (local, swap to S3 later)
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Shiprocket (Phase 5)
    SHIPROCKET_EMAIL: str = ""
    SHIPROCKET_PASSWORD: str = ""
    SHIPROCKET_BASE_URL: str = "https://apiv2.shiprocket.in/v1/external"

    # Razorpay (Phase 6)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
