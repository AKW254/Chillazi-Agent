from __future__ import annotations

from typing import List

from langchain_core.tools import BaseTool, StructuredTool

from app.config.database import db_session
from app.schemas.menu_schema import MenuItemCreate
from app.services.menu_service import MenuService
from app.tools._shared import audit_tool, serialize_menu_item, tool_response


def build_menu_tools(admin: bool = False) -> List[BaseTool]:
    actor = "admin" if admin else "guest"

    @audit_tool("menu.get_menu", actor=actor)
    def get_menu() -> str:
        try:
            with db_session() as db:
                service = MenuService(db)
                items = service.list_menu_items()
                return tool_response(
                    True,
                    "Menu retrieved successfully",
                    [serialize_menu_item(item) for item in items],
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to retrieve menu",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("menu.get_menu_item", actor=actor)
    def get_menu_item(item_id: int) -> str:
        if item_id <= 0:
            return tool_response(
                False,
                "Menu item id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = MenuService(db)
                item = service.get_menu_item(item_id)
                if not item:
                    return tool_response(False, "Menu item not found")
                return tool_response(
                    True,
                    "Menu item retrieved successfully",
                    serialize_menu_item(item),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to retrieve menu item",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("menu.create_menu_item", actor=actor)
    def create_menu_item(
        name: str,
        price: float,
        description: str | None = None,
    ) -> str:
        if not name.strip():
            return tool_response(
                False,
                "Menu item name cannot be empty",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = MenuService(db)
                item = service.create_menu_item(
                    MenuItemCreate(
                        name=name.strip(),
                        description=description,
                        price=price,
                    )
                )
                return tool_response(
                    True,
                    "Menu item created successfully",
                    serialize_menu_item(item),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to create menu item",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("menu.update_menu_item", actor=actor)
    def update_menu_item(
        item_id: int,
        name: str,
        price: float,
        description: str | None = None,
    ) -> str:
        if item_id <= 0:
            return tool_response(
                False,
                "Menu item id must be a positive integer",
                error="ValidationError",
            )
        if not name.strip():
            return tool_response(
                False,
                "Menu item name cannot be empty",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = MenuService(db)
                item = service.update_menu_item(
                    item_id,
                    MenuItemCreate(
                        name=name.strip(),
                        description=description,
                        price=price,
                    ),
                )
                if not item:
                    return tool_response(False, "Menu item not found")
                return tool_response(
                    True,
                    "Menu item updated successfully",
                    serialize_menu_item(item),
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to update menu item",
                error=f"{type(exc).__name__}: {exc}",
            )

    @audit_tool("menu.delete_menu_item", actor=actor)
    def delete_menu_item(item_id: int) -> str:
        if item_id <= 0:
            return tool_response(
                False,
                "Menu item id must be a positive integer",
                error="ValidationError",
            )

        try:
            with db_session() as db:
                service = MenuService(db)
                ok = service.delete_menu_item(item_id)
                if not ok:
                    return tool_response(False, "Menu item not found")
                return tool_response(
                    True,
                    "Menu item deleted successfully",
                    {"item_id": item_id},
                )
        except Exception as exc:
            return tool_response(
                False,
                "Failed to delete menu item",
                error=f"{type(exc).__name__}: {exc}",
            )

    tools: List[BaseTool] = [
        StructuredTool.from_function(
            func=get_menu,
            name="get_menu",
            description="List all available menu items.",
        ),
        StructuredTool.from_function(
            func=get_menu_item,
            name="get_menu_item",
            description="Get a single menu item by its id.",
        ),
    ]

    if admin:
        tools.extend(
            [
                StructuredTool.from_function(
                    func=create_menu_item,
                    name="create_menu_item",
                    description="Create a new menu item. Admin only.",
                ),
                StructuredTool.from_function(
                    func=update_menu_item,
                    name="update_menu_item",
                    description="Update an existing menu item. Admin only.",
                ),
                StructuredTool.from_function(
                    func=delete_menu_item,
                    name="delete_menu_item",
                    description="Delete a menu item by id. Admin only.",
                ),
            ]
        )

    return tools
