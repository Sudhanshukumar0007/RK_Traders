import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.catalog import ProductVariant, Product, ProductImage
from app.models.cart import Cart, CartItem
from app.models.user import User
from app.routers.auth import get_current_user, get_optional_current_user
from app.services.pricing import calculate_price
from app.schemas.cart import CartRead, CartItemAdd, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["Cart"])


class CartMergeRequest(BaseModel):
    session_token: Optional[str] = None


def get_variant_price(variant: ProductVariant, quantity: int, is_wholesale_customer: bool = False):
    min_qty = 1 if (is_wholesale_customer and variant.wholesale_price is not None) else variant.wholesale_min_qty
    return calculate_price(
        variant_id=variant.id,
        quantity=quantity,
        mrp=float(variant.mrp),
        wholesale_price=float(variant.wholesale_price) if variant.wholesale_price is not None else None,
        wholesale_min_qty=min_qty,
    )


async def get_cart_response(db: AsyncSession, cart: Cart, is_wholesale_customer: bool = False) -> CartRead:
    # Reload cart with relations to compute live prices
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
            .selectinload(Product.images)
        )
        .where(Cart.id == cart.id)
    )
    cart_full = result.scalar_one()

    items_read = []
    subtotal = 0.0
    item_count = 0

    for item in cart_full.items:
        # Calculate dynamic live price using pricing service
        price_breakdown = get_variant_price(item.variant, item.quantity, is_wholesale_customer)
        subtotal += price_breakdown.total_price
        item_count += item.quantity

        # Find primary image
        primary_image = next(
            (img.image_url for img in item.variant.product.images if img.is_primary),
            None
        )
        if not primary_image and item.variant.product.images:
            primary_image = item.variant.product.images[0].image_url

        items_read.append({
            "id": item.id,
            "cart_id": item.cart_id,
            "variant_id": item.variant_id,
            "quantity": item.quantity,
            "price_snapshot": item.price_snapshot,
            "added_at": item.added_at,
            "live_price": price_breakdown,
            "product_name": item.variant.product.name,
            "sku": item.variant.sku,
            "size_label": item.variant.size_label,
            "primary_image_url": primary_image
        })

    return CartRead(
        id=cart_full.id,
        user_id=cart_full.user_id,
        session_token=cart_full.session_token,
        items=items_read,
        item_count=item_count,
        subtotal=subtotal,
        created_at=cart_full.created_at,
        updated_at=cart_full.updated_at
    )


async def get_or_create_cart(
    db: AsyncSession,
    user: Optional[User],
    session_token: Optional[str],
    response: Response
) -> tuple[Cart, str | None]:
    """Helper to fetch or create the active cart, returning (cart, new_session_token_to_set)"""
    new_token = None

    if user:
        # Get authenticated user's cart
        result = await db.execute(select(Cart).where(Cart.user_id == user.id))
        cart = result.scalar_one_or_none()
        if not cart:
            cart = Cart(user_id=user.id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        return cart, None
    else:
        # Get or create guest cart
        cart = None
        if session_token:
            result = await db.execute(select(Cart).where(Cart.session_token == session_token))
            cart = result.scalar_one_or_none()

        if not cart:
            new_token = str(uuid.uuid4())
            cart = Cart(session_token=new_token)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
            response.set_cookie(
                key="cart_session",
                value=new_token,
                httponly=True,
                max_age=30 * 24 * 60 * 60, # 30 days
                samesite="lax",
            )
        return cart, new_token


@router.get("", response_model=CartRead)
async def get_cart(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)] = None,
    cart_session: Annotated[Optional[str], Cookie()] = None,
):
    cart, _ = await get_or_create_cart(db, current_user, cart_session, response)
    is_wholesale = current_user.is_wholesale_customer if current_user else False
    return await get_cart_response(db, cart, is_wholesale)


@router.post("/items", response_model=CartRead)
async def add_cart_item(
    item_in: CartItemAdd,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)] = None,
    cart_session: Annotated[Optional[str], Cookie()] = None,
):
    # Verify variant exists and is active
    result = await db.execute(
        select(ProductVariant)
        .options(selectinload(ProductVariant.product))
        .where(ProductVariant.id == item_in.variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant or not variant.is_active or not variant.product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found or inactive",
        )

    cart, _ = await get_or_create_cart(db, current_user, cart_session, response)
    is_wholesale = current_user.is_wholesale_customer if current_user else False

    # Check if item is already in cart
    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant.id)
    )
    cart_item = result.scalar_one_or_none()

    if cart_item:
        cart_item.quantity += item_in.quantity
    else:
        # Snapshot the current price based on quantity added
        price_breakdown = get_variant_price(variant, item_in.quantity, is_wholesale)
        cart_item = CartItem(
            cart_id=cart.id,
            variant_id=variant.id,
            quantity=item_in.quantity,
            price_snapshot=price_breakdown.unit_price
        )
        db.add(cart_item)

    await db.commit()
    return await get_cart_response(db, cart, is_wholesale)


@router.patch("/items/{item_id}", response_model=CartRead)
async def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)] = None,
    cart_session: Annotated[Optional[str], Cookie()] = None,
):
    # Find user's cart
    if current_user:
        result = await db.execute(select(Cart).where(Cart.user_id == current_user.id))
    else:
        if not cart_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        result = await db.execute(select(Cart).where(Cart.session_token == cart_session))

    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    # Find the cart item
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.variant))
        .where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    is_wholesale = current_user.is_wholesale_customer if current_user else False
    cart_item.quantity = item_in.quantity

    # Update price snapshot
    price_breakdown = get_variant_price(cart_item.variant, item_in.quantity, is_wholesale)
    cart_item.price_snapshot = price_breakdown.unit_price

    await db.commit()
    return await get_cart_response(db, cart, is_wholesale)


@router.delete("/items/{item_id}", response_model=CartRead)
async def delete_cart_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)] = None,
    cart_session: Annotated[Optional[str], Cookie()] = None,
):
    # Find user's cart
    if current_user:
        result = await db.execute(select(Cart).where(Cart.user_id == current_user.id))
    else:
        if not cart_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        result = await db.execute(select(Cart).where(Cart.session_token == cart_session))

    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()

    is_wholesale = current_user.is_wholesale_customer if current_user else False
    return await get_cart_response(db, cart, is_wholesale)


@router.post("/merge", response_model=CartRead)
async def merge_cart(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    merge_req: Optional[CartMergeRequest] = None,
    cart_session: Annotated[Optional[str], Cookie()] = None,
):
    # Determine the guest token from body or cookie
    session_token = (merge_req.session_token if merge_req else None) or cart_session
    if not session_token:
        # No guest session to merge, just return user's cart
        user_cart, _ = await get_or_create_cart(db, current_user, None, response)
        return await get_cart_response(db, user_cart, current_user.is_wholesale_customer)

    # Find the guest cart
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.session_token == session_token)
    )
    guest_cart = result.scalar_one_or_none()

    # Get or create user's cart
    user_cart, _ = await get_or_create_cart(db, current_user, None, response)

    if guest_cart and guest_cart.items:
        # Load user's cart items to identify duplicates
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == user_cart.id)
        )
        user_items = {item.variant_id: item for item in result.scalars().all()}

        for guest_item in guest_cart.items:
            if guest_item.variant_id in user_items:
                # Quantities are summed
                user_item = user_items[guest_item.variant_id]
                user_item.quantity += guest_item.quantity
                # Update price snapshot using the new combined quantity
                result = await db.execute(
                    select(ProductVariant).where(ProductVariant.id == user_item.variant_id)
                )
                variant = result.scalar_one()
                price_breakdown = get_variant_price(
                    variant, user_item.quantity, current_user.is_wholesale_customer
                )
                user_item.price_snapshot = price_breakdown.unit_price
            else:
                # Fetch variant to snapshot price
                result = await db.execute(
                    select(ProductVariant).where(ProductVariant.id == guest_item.variant_id)
                )
                variant = result.scalar_one()
                price_breakdown = get_variant_price(
                    variant, guest_item.quantity, current_user.is_wholesale_customer
                )
                new_item = CartItem(
                    cart_id=user_cart.id,
                    variant_id=guest_item.variant_id,
                    quantity=guest_item.quantity,
                    price_snapshot=price_breakdown.unit_price
                )
                db.add(new_item)

        # Delete guest cart items and the guest cart itself
        await db.execute(delete(CartItem).where(CartItem.cart_id == guest_cart.id))
        await db.delete(guest_cart)
        await db.commit()

    # Clear the guest session token cookie
    response.delete_cookie(key="cart_session")

    return await get_cart_response(db, user_cart, current_user.is_wholesale_customer)
