"""
Pydantic schemas for User and Address.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─── Address ─────────────────────────────────────────────────────────────────

class AddressBase(BaseModel):
    label: str = Field("Home", max_length=50)
    full_address: str = Field(..., min_length=5, max_length=1000)
    city: str = Field(..., min_length=1, max_length=200)
    state: str = Field(..., min_length=1, max_length=200)
    pincode: str = Field(..., min_length=6, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=50)
    full_address: Optional[str] = Field(None, min_length=5, max_length=1000)
    city: Optional[str] = Field(None, min_length=1, max_length=200)
    state: Optional[str] = Field(None, min_length=1, max_length=200)
    pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None


class AddressRead(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime


# ─── User ────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    is_wholesale_customer: Optional[bool] = None  # admin-settable


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_admin: bool
    is_wholesale_customer: bool
    created_at: datetime
    updated_at: datetime
    addresses: list[AddressRead] = []


# ─── Auth token responses ─────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
