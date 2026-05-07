from typing import List

from langchain_core.tools import BaseTool

from app.api.dependencies.auth import ROLE_ADMIN, ROLE_GUEST, ROLE_USER
from app.tools.cart_tools import build_cart_tools
from app.tools.menu_tools import build_menu_tools
from app.tools.order_tools import build_admin_order_tools, build_user_order_tools


def get_tools_by_role(role: str, current_user_id: int | None = None) -> List[BaseTool]:
    """Return tools dynamically based on the authenticated user's role."""

    normalized_role = (role or ROLE_GUEST).strip().lower()
    common_tools = build_menu_tools(admin=False)

    if normalized_role == ROLE_ADMIN:
        admin_menu_tools = build_menu_tools(admin=True)[len(common_tools):]
        return common_tools + admin_menu_tools + build_admin_order_tools()

    if normalized_role == ROLE_USER:
        if current_user_id is None:
            raise ValueError("current_user_id is required for user tools")
        return common_tools + build_cart_tools(current_user_id) + build_user_order_tools(current_user_id)

    return common_tools
