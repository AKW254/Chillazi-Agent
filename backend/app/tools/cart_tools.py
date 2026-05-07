from __future__ import annotations

from typing import List

from langchain_core.tools import BaseTool, StructuredTool

from app.config.database import db_session
from app.schemas.cart_schema import CartItemCreate
from app.services.cart_service import CartService
from app.tools._shared import (
    audit_tool,
    serialize_cart,
    serialize_cart_item,
    tool_response,
)


def build_cart_tools(current_user_id: int) -> List[BaseTool]:
    @audit_tool("cart.get_cart", user_id=current_user_id)
    def get_cart() -> str:
        try:
            with db_session() as db:
                service = CartService(db)
                cart = service.get_or_create_cart(current_user_id)
                return tool_response(
                    True,
                    "Cart retrieved successfully",
                    serialize_cart(cart),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to retrieve cart",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("cart.add_to_cart", user_id=current_user_id)
    def add_to_cart(menu_item_id: int, quantity: int) -> str:
        if menu_item_id <= 0:
            return tool_response(
                False,
                "Menu item id must be a positive integer",
                error="ValidationError",
            )
        if quantity <= 0:
            return tool_response(
                False,
                "Quantity must be greater than zero",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = CartService(db)
                cart = service.get_or_create_cart(current_user_id)
                item = service.add_item_to_cart(
                    cart.id,
                    CartItemCreate(menu_item_id=menu_item_id, quantity=quantity),
                )
                if not item:
                    return tool_response(False, "Menu item not found")
                refreshed_cart = service.get_cart(cart.id)
                return tool_response(
                    True,
                    "Item added to cart",
                    {
                        "cart": serialize_cart(refreshed_cart),
                        "item": serialize_cart_item(item),
                    },
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to add item to cart",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("cart.update_cart_item", user_id=current_user_id)
    def update_cart_item(menu_item_id: int, quantity: int) -> str:
        if menu_item_id <= 0:
            return tool_response(
                False,
                "Menu item id must be a positive integer",
                error="ValidationError",
            )
        if quantity <= 0:
            return tool_response(
                False,
                "Quantity must be greater than zero",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = CartService(db)
                cart = service.get_cart_by_user(current_user_id)
                if not cart:
                    return tool_response(False, "Cart not found")
                item = service.update_item_quantity(cart.id, menu_item_id, quantity)
                if not item:
                    return tool_response(False, "Item not found in cart")
                refreshed_cart = service.get_cart(cart.id)
                return tool_response(
                    True,
                    "Cart item updated successfully",
                    {
                        "cart": serialize_cart(refreshed_cart),
                        "item": serialize_cart_item(item),
                    },
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to update cart item",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("cart.remove_from_cart", user_id=current_user_id)
    def remove_from_cart(menu_item_id: int) -> str:
        if menu_item_id <= 0:
            return tool_response(
                False,
                "Menu item id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = CartService(db)
                cart = service.get_cart_by_user(current_user_id)
                if not cart:
                    return tool_response(False, "Cart not found")
                ok = service.remove_item_from_cart(cart.id, menu_item_id)
                if not ok:
                    return tool_response(False, "Item not found in cart")
                refreshed_cart = service.get_cart(cart.id)
                return tool_response(
                    True,
                    "Item removed from cart",
                    serialize_cart(refreshed_cart),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to remove item from cart",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("cart.clear_cart", user_id=current_user_id)
    def clear_cart() -> str:
        try:
            with db_session() as db:
                service = CartService(db)
                cart = service.get_cart_by_user(current_user_id)
                if not cart:
                    return tool_response(False, "Cart not found")
                ok = service.clear_cart(cart.id)
                if not ok:
                    return tool_response(False, "Cart not found")
                refreshed_cart = service.get_cart(cart.id)
                return tool_response(
                    True,
                    "Cart cleared successfully",
                    serialize_cart(refreshed_cart),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to clear cart",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("cart.delete_cart", user_id=current_user_id)
    def delete_cart() -> str:
        try:
            with db_session() as db:
                service = CartService(db)
                cart = service.get_cart_by_user(current_user_id)
                if not cart:
                    return tool_response(False, "Cart not found")
                ok = service.delete_cart(cart.id)
                if not ok:
                    return tool_response(False, "Cart not found")
                return tool_response(
                    True,
                    "Cart deleted successfully",
                    {"cart_id": cart.id},
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to delete cart",
                error=f"{type(exc).__name__}: {exc}",
            )

    return [
        StructuredTool.from_function(
            func=get_cart,
            name="get_cart",
            description="Get the current user's cart, creating it if needed.",
        ),
        StructuredTool.from_function(
            func=add_to_cart,
            name="add_to_cart",
            description="Add a menu item to the current user's cart.",
        ),
        StructuredTool.from_function(
            func=update_cart_item,
            name="update_cart_item",
            description="Update the quantity of a menu item in the current user's cart.",
        ),
        StructuredTool.from_function(
            func=remove_from_cart,
            name="remove_from_cart",
            description="Remove a menu item from the current user's cart.",
        ),
        StructuredTool.from_function(
            func=clear_cart,
            name="clear_cart",
            description="Remove all items from the current user's cart.",
        ),
        StructuredTool.from_function(
            func=delete_cart,
            name="delete_cart",
            description="Delete the current user's cart entirely.",
        ),
    ]
