from __future__ import annotations

from typing import List

from langchain_core.tools import BaseTool, StructuredTool

from app.config.database import db_session
from app.schemas.order_schema import OrderStatus
from app.services.cart_service import CartService
from app.services.mailer.mailer import create_mailer
from app.services.order_service import (
    OrderNotFoundError,
    OrderService,
    OrderValidationError,
)
#Convert DB objects → JSON-safe output for LLM
from app.tools._shared import (
    audit_tool,
    serialize_order,
    serialize_order_summary,
    tool_response,
)


def build_user_order_tools(current_user_id: int) -> List[BaseTool]:
    def _clear_current_cart(db) -> bool:
        cart_service = CartService(db)
        cart = cart_service.get_cart_by_user(current_user_id)
        if not cart:
            return False
        return cart_service.clear_cart(cart.id)

    @audit_tool("order.place_order", user_id=current_user_id)
    def place_order(
        delivery_address: str | None = None,
        notes: str | None = None,
        clear_cart: bool = True,
    ) -> str:
        try:
            with db_session() as db:
                mailer = create_mailer()
                service = OrderService(db, mailer)
                order = service.create_order_from_cart(
                    user_id=current_user_id,
                    delivery_address=delivery_address,
                    notes=notes,
                    clear_cart=clear_cart,
                )
                cart_cleared = False
                if clear_cart:
                    cart_cleared = _clear_current_cart(db)
                if getattr(order, "_duplicate_checkout", False):
                    message = (
                        "A similar order was already placed recently, so the existing order was returned instead of creating a duplicate."
                    )
                    if clear_cart:
                        message += " The cart was cleared." if cart_cleared else " The cart could not be verified after checkout."
                    return tool_response(
                        True,
                        message,
                        serialize_order(order),
                    )
                message = "Order placed successfully"
                if clear_cart:
                    message += " The cart was cleared." if cart_cleared else " The cart could not be verified after checkout."
                return tool_response(
                    True,
                    message,
                    serialize_order(order),
                )
        except OrderNotFoundError as exc:
            return tool_response(False, str(exc), error=type(exc).__name__)
        except OrderValidationError as exc:
            return tool_response(False, str(exc), error=type(exc).__name__)
        except ValueError as exc:
            return tool_response(False, str(exc), error=type(exc).__name__)
        except Exception as exc:
            return tool_response(
                False,
                "Failed to place order",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("order.get_order", user_id=current_user_id)
    def get_order(order_id: int) -> str:
        if order_id <= 0:
            return tool_response(
                False,
                "Order id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = OrderService(db)
                order = service.get_order(order_id)
                if not order:
                    return tool_response(False, "Order not found")
                if order.user_id != current_user_id:
                    return tool_response(
                        False,
                        "You can only access your own orders",
                        error="PermissionError",
                    )
                return tool_response(
                    True,
                    "Order retrieved successfully",
                    serialize_order(order),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to retrieve order",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("order.list_my_orders", user_id=current_user_id)
    def list_my_orders(skip: int = 0, limit: int = 20) -> str:
        if skip < 0:
            return tool_response(
                False,
                "Skip must be zero or greater",
                error="ValidationError",
            )
        if limit <= 0:
            return tool_response(
                False,
                "Limit must be greater than zero",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = OrderService(db)
                orders = service.list_orders(
                    user_id=current_user_id,
                    skip=skip,
                    limit=limit,
                )
                return tool_response(
                    True,
                    "Orders retrieved successfully",
                    [serialize_order_summary(order) for order in orders],
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to list orders",
                error=f"{type(exc).__name__}: {exc}",
            )
    @audit_tool("order.cancel_order", user_id=current_user_id)
    def cancel_order(
        order_id: int,
        status: str | None = None,
        reason: str | None = None,
    ) -> str:
        if order_id <= 0:
            return tool_response(
                False,
                "Order id must be a positive integer",
                error="ValidationError",
            )

        normalized_status = "cancelled" if status is None else status.strip().lower()
        if normalized_status in {"canceled", "cancel"}:
            normalized_status = "cancelled"
        if normalized_status != "cancelled":
            return tool_response(
                False,
                "cancel_order only supports changing the order to cancelled",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                mailer = create_mailer()
                service = OrderService(db, mailer)
                order = service.cancel_order(
                    order_id,
                    current_user_id,
                    reason=reason,
                )
                if not order:
                    return tool_response(False, "Order not found")
                if getattr(order, "_already_cancelled", False):
                    return tool_response(
                        True,
                        "Order is already cancelled",
                        serialize_order(order),
                    )
                return tool_response(
                    True,
                    "Order cancelled successfully",
                    serialize_order(order),
                )
        except OrderNotFoundError as exc:
            return tool_response(False, str(exc), error=type(exc).__name__)
        except OrderValidationError as exc:
            return tool_response(False, str(exc), error=type(exc).__name__)
        except Exception as exc:
            return tool_response(
                False,
                "Failed to cancel order",
                error=f"{type(exc).__name__}: {exc}",
            )

    return [
        #It converts normal Python functions into AI-function-calling endpoints
        StructuredTool.from_function(
            func=place_order,
            name="place_order",
            description="Checkout the current user's cart and create an order.",
        ),
        StructuredTool.from_function(
            func=get_order,
            name="get_order",
            description="Get one of the current user's orders by id.",
        ),
        StructuredTool.from_function(
            func=list_my_orders,
            name="list_my_orders",
            description="List the current user's orders.",
        ),
        StructuredTool.from_function(
            func=cancel_order,
            name="cancel_order",
            description="Cancel an order by id. Only allowed for the user who placed the order.",
        ),
    ]


def build_admin_order_tools() -> List[BaseTool]:
    @audit_tool("order.get_order", actor="admin")
    def get_order(order_id: int) -> str:
        if order_id <= 0:
            return tool_response(
                False,
                "Order id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = OrderService(db)
                order = service.get_order(order_id)
                if not order:
                    return tool_response(False, "Order not found")
                return tool_response(
                    True,
                    "Order retrieved successfully",
                    serialize_order(order),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to retrieve order",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("order.list_orders", actor="admin")
    def list_orders(
        skip: int = 0,
        limit: int = 20,
        user_id: int | None = None,
    ) -> str:
        if skip < 0:
            return tool_response(
                False,
                "Skip must be zero or greater",
                error="ValidationError",
            )
        if limit <= 0:
            return tool_response(
                False,
                "Limit must be greater than zero",
                error="ValidationError",
            )
        if user_id is not None and user_id <= 0:
            return tool_response(
                False,
                "User id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = OrderService(db)
                orders = service.list_orders(
                    user_id=user_id,
                    skip=skip,
                    limit=limit,
                )
                return tool_response(
                    True,
                    "Orders retrieved successfully",
                    [serialize_order_summary(order) for order in orders],
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to list orders",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("order.update_order_status", actor="admin")
    def update_order_status(
        order_id: int,
        status: OrderStatus,
        reason: str | None = None,
    ) -> str:
        if order_id <= 0:
            return tool_response(
                False,
                "Order id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                mailer = create_mailer()
                service = OrderService(db, mailer)
                order = service.update_order_status(order_id, status, reason)
                if not order:
                    return tool_response(False, "Order not found")
                return tool_response(
                    True,
                    "Order status updated successfully",
                    serialize_order(order),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to update order status",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("order.delete_order", actor="admin")
    def delete_order(order_id: int) -> str:
        if order_id <= 0:
            return tool_response(
                False,
                "Order id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = OrderService(db)
                ok = service.delete_order(order_id)
                if not ok:
                    return tool_response(False, "Order not found")
                return tool_response(
                    True,
                    "Order deleted successfully",
                    {"order_id": order_id},
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to delete order",
                error=f"{type(exc).__name__}: {exc}",
            )

    return [
        StructuredTool.from_function(
            func=get_order,
            name="get_order",
            description="Get any order by id. Admin only.",
        ),
        StructuredTool.from_function(
            func=list_orders,
            name="list_orders",
            description="List orders with optional pagination and user filter. Admin only.",
        ),
        StructuredTool.from_function(
            func=update_order_status,
            name="update_order_status",
            description="Update an order status. Admin only.",
        ),
        StructuredTool.from_function(
            func=delete_order,
            name="delete_order",
            description="Delete an order by id. Admin only.",
        ),
    ]
