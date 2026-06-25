from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import get_db
from app.models.user import Address, User
from app.routers.auth import get_current_user
from app.schemas.user import AddressCreate, AddressUpdate, AddressRead

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_in: AddressCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # If this address is set to default, unset all other default addresses for this user
    if address_in.is_default:
        await db.execute(
            update(Address)
            .where(Address.user_id == current_user.id)
            .values(is_default=False)
        )

    db_address = Address(
        user_id=current_user.id,
        label=address_in.label,
        full_address=address_in.full_address,
        city=address_in.city,
        state=address_in.state,
        pincode=address_in.pincode,
        phone=address_in.phone,
        is_default=address_in.is_default,
    )
    db.add(db_address)
    await db.commit()
    await db.refresh(db_address)
    return db_address


@router.get("", response_model=list[AddressRead])
async def list_addresses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Address)
        .where(Address.user_id == current_user.id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: int,
    address_in: AddressUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Address)
        .where(Address.id == address_id, Address.user_id == current_user.id)
    )
    address = result.scalar_one_or_none()
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    # If setting to default, unset other defaults
    if address_in.is_default:
        await db.execute(
            update(Address)
            .where(Address.user_id == current_user.id)
            .values(is_default=False)
        )

    # Apply updates
    update_data = address_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)

    await db.commit()
    await db.refresh(address)
    return address


@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Address)
        .where(Address.id == address_id, Address.user_id == current_user.id)
    )
    address = result.scalar_one_or_none()
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    await db.delete(address)
    await db.commit()
    return {"status": "success", "message": "Address deleted"}
