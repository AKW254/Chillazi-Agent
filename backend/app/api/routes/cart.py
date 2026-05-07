from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.auth import ROLE_ADMIN, ROLE_USER, get_role_name, require_roles
from app.config.database import get_db
from app.models import User
from app.schemas.cart_schema import CartItemCreate, CartResponse,CartItemUpdateQuantity,CartItemResponse
from app.services.cart_service import CartService

router = APIRouter()


def _ensure_cart_owner(service: CartService, cart_id: int, current_user: User):
    cart = service.get_cart(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if cart.user_id != current_user.id and get_role_name(current_user) != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="You can only access your own cart")
    return cart

# Admin cart list
@router.get("/", response_model=list[CartResponse])
def list_carts(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(ROLE_ADMIN)),
):
    service = CartService(db)
    try:
        return service.list_carts(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    service = CartService(db)
    try:
        return _ensure_cart_owner(service, cart_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#Get cart by user id, create if not exists
@router.get("/user/{user_id}", response_model=CartResponse)
def get_or_create_cart(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Get user's cart, creating one if needed."""
    if user_id != current_user.id and get_role_name(current_user) != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="You can only access your own cart")

    service = CartService(db)
    try:
        cart = service.get_or_create_cart(user_id)
        return cart
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/items", response_model=CartItemResponse)
def add_item_to_cart(
    user_id: int,
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Add item to user's cart (auto-creates cart if needed)."""
    if user_id != current_user.id and get_role_name(current_user) != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="You can only add items to your own cart")

    service = CartService(db)
    try:
        cart = service.get_or_create_cart(user_id)
        added_item = service.add_item_to_cart(cart.id, item)
        if not added_item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return added_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{cart_id}/items/{menu_item_id}", response_model=CartItemResponse)
def update_item_quantity(
    cart_id: int,
    menu_item_id: int,
    cart: CartItemUpdateQuantity,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Update quantity of item in cart."""
    service = CartService(db)
    try:
        _ensure_cart_owner(service, cart_id, current_user)
        item = service.update_item_quantity(cart_id, menu_item_id, cart.quantity)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cart_id}/items/{menu_item_id}")
def remove_item_from_cart(
    cart_id: int,
    menu_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Remove item from cart."""
    service = CartService(db)
    try:
        _ensure_cart_owner(service, cart_id, current_user)
        ok = service.remove_item_from_cart(cart_id, menu_item_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        return {"detail": "Item removed from cart"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{cart_id}/clear")
def clear_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Clear all items from cart."""
    service = CartService(db)
    try:
        _ensure_cart_owner(service, cart_id, current_user)
        ok = service.clear_cart(cart_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Cart not found")
        return {"detail": "Cart cleared"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cart_id}")
def delete_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Delete entire cart."""
    service = CartService(db)
    try:
        _ensure_cart_owner(service, cart_id, current_user)
        ok = service.delete_cart(cart_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Cart not found")
        return {"detail": "Cart deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
