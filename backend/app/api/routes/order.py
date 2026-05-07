import traceback

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    ROLE_ADMIN,
    ROLE_USER,
    ensure_self_or_admin,
    get_role_name,
    require_roles,
)
from app.config.database import get_db
from app.config.settings import settings
from app.models import User
from app.schemas.order_schema import (
    OrderCheckoutRequest,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.mailer.mailer import create_mailer
from app.services.order_service import (
    OrderNotFoundError,
    OrderService,
    OrderValidationError,
)
from app.utils.logger import logger


router = APIRouter(tags=["Orders"])


def _to_order_list_response(order) -> OrderListResponse:
    return OrderListResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        item_count=len(order.items),
    )


def _ensure_order_access(order, current_user: User) -> None:
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.user_id != current_user.id and get_role_name(current_user) != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own orders",
        )


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout_from_cart(
    checkout: OrderCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER)),
):
    """
    Create an order from the authenticated user's cart.

    `cart_id` is optional, but if provided it must belong to the current user.
    """
    service = OrderService(db, create_mailer())

    if checkout.user_id is not None and checkout.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only checkout with your own account",
        )

    logger.info(
        f"Checkout initiated: user_id={current_user.id}, cart_id={checkout.cart_id}"
    )

    try:
        order = service.create_order_from_cart(
            user_id=current_user.id,
            cart_id=checkout.cart_id,
            delivery_address=checkout.delivery_address,
            notes=checkout.notes,
            clear_cart=True,
        )
        logger.info(
            f"Checkout completed: order_id={order.id}, user_id={order.user_id}, total={order.total_amount}"
        )
        return order
    except OrderNotFoundError as exc:
        logger.warning(f"Checkout validation failed - not found: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except OrderValidationError as exc:
        logger.warning(f"Checkout validation failed: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ValueError as exc:
        logger.warning(f"Checkout value error: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except HTTPException:
        raise
    except Exception as exc:
        error_msg = str(exc)
        error_type = type(exc).__name__
        tb = traceback.format_exc()

        logger.error(
            f"Checkout failed with {error_type}: {error_msg}\n"
            f"User: {current_user.id}, Cart: {checkout.cart_id}\n"
            f"Traceback:\n{tb}"
        )

        detail = error_msg if settings.debug else "Checkout failed. Please try again."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


@router.get("/", response_model=list[OrderListResponse])
def list_all_orders(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Items to return"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Admin-only endpoint for viewing all orders."""
    service = OrderService(db)
    logger.debug(f"Listing all orders: skip={skip}, limit={limit}")

    try:
        orders = service.list_orders(skip=skip, limit=limit)
        return [_to_order_list_response(order) for order in orders]
    except Exception as exc:
        logger.error(f"Error listing all orders: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list orders",
        )


@router.get("/me", response_model=list[OrderListResponse])
def list_my_orders(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """List orders that belong to the authenticated user."""
    service = OrderService(db)
    logger.debug(
        f"Listing orders for authenticated user: user_id={current_user.id}, skip={skip}, limit={limit}"
    )

    try:
        orders = service.list_orders(user_id=current_user.id, skip=skip, limit=limit)
        return [_to_order_list_response(order) for order in orders]
    except Exception as exc:
        logger.error(
            f"Error listing orders for authenticated user {current_user.id}: {str(exc)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list orders",
        )


@router.get("/user/{user_id}", response_model=list[OrderListResponse])
def list_user_orders(
    user_id: int,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """
    List orders for a specific user.

    Regular users can only view their own orders. Admins can view any user's orders.
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must be a positive integer",
        )

    ensure_self_or_admin(current_user, user_id)

    service = OrderService(db)
    logger.debug(f"Listing orders for user: user_id={user_id}, skip={skip}, limit={limit}")

    try:
        orders = service.list_orders(user_id=user_id, skip=skip, limit=limit)
        return [_to_order_list_response(order) for order in orders]
    except Exception as exc:
        logger.error(f"Error listing orders for user {user_id}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list orders",
        )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
):
    """Get a single order. Users can only access their own orders."""
    if order_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order ID must be a positive integer",
        )

    service = OrderService(db)
    logger.debug(f"Retrieving order: order_id={order_id}")

    try:
        order = service.get_order(order_id)
        _ensure_order_access(order, current_user)
        logger.debug(f"Order retrieved: order_id={order_id}")
        return order
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving order {order_id}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order",
        )


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Admin-only order status management."""
    if order_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order ID must be a positive integer",
        )

    service = OrderService(db, create_mailer())
    logger.info(
        f"Status update requested: order_id={order_id}, status={status_update.status}, reason={status_update.reason}"
    )

    try:
        updated = service.update_order_status(
            order_id, status_update.status, status_update.reason
        )
        if not updated:
            logger.warning(f"Order not found for status update: order_id={order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        logger.info(
            f"Order status updated: order_id={order_id}, status={status_update.status}"
        )
        return updated
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error updating order status: order_id={order_id}, {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status",
        )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Admin-only order deletion."""
    if order_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order ID must be a positive integer",
        )

    service = OrderService(db)
    logger.info(f"Delete requested: order_id={order_id}")

    try:
        ok = service.delete_order(order_id)
        if not ok:
            logger.warning(f"Order not found for deletion: order_id={order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        logger.info(f"Order deleted: order_id={order_id}")
        return None
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error deleting order {order_id}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete order",
        )
