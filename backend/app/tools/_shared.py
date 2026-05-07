from __future__ import annotations

import hashlib
import json
import time
from functools import wraps
from datetime import datetime
from typing import Any, Callable, Iterable

from app.utils.logger import logger


def tool_response(
    success: bool,
    message: str,
    data: Any = None,
    error: str | None = None,
) -> str:
    payload: dict[str, Any] = {
        "success": success,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error
    return json.dumps(payload, ensure_ascii=False, default=str)


def log_tool_event(
    tool_name: str,
    action: str,
    *,
    status: str,
    actor: str | None = None,
    user_id: int | None = None,
    details: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "action": action,
        "status": status,
    }
    if actor is not None:
        payload["actor"] = actor
    if user_id is not None:
        payload["user_id"] = user_id
    if details:
        payload["details"] = details
    if error is not None:
        payload["error"] = error

    message = f"TOOL_AUDIT {json.dumps(payload, ensure_ascii=False, default=str)}"
    if status in {"failed", "error", "blocked"}:
        logger.warning(message)
    else:
        logger.info(message)


def audit_tool(
    tool_name: str,
    *,
    actor: str | None = None,
    user_id: int | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            started = time.perf_counter()
            log_tool_event(
                tool_name,
                func.__name__,
                status="started",
                actor=actor,
                user_id=user_id,
                details={"inputs": kwargs},
            )

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                log_tool_event(
                    tool_name,
                    func.__name__,
                    status="error",
                    actor=actor,
                    user_id=user_id,
                    details={"duration_ms": round((time.perf_counter() - started) * 1000, 2)},
                    error=f"{type(exc).__name__}: {exc}",
                )
                raise

            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            details: dict[str, Any] = {"duration_ms": duration_ms}
            status = "success"

            if isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict):
                        details["result_message"] = parsed.get("message")
                        details["has_data"] = "data" in parsed
                        success = parsed.get("success")
                        if success is False:
                            status = "failed"
                        elif success is True:
                            status = "success"
                    else:
                        details["result_preview"] = result[:200]
                except json.JSONDecodeError:
                    details["result_preview"] = result[:200]
            else:
                details["result_type"] = type(result).__name__

            log_tool_event(
                tool_name,
                func.__name__,
                status=status,
                actor=actor,
                user_id=user_id,
                details=details,
            )
            return result

        return wrapper

    return decorator


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.split()).casefold()


def build_order_signature(
    user_id: int,
    items: Iterable[Any],
    *,
    delivery_address: str | None = None,
    notes: str | None = None,
) -> str:
    normalized_items = sorted(
        [
            {
                "menu_item_id": int(getattr(item, "menu_item_id")),
                "quantity": int(getattr(item, "quantity")),
            }
            for item in items
        ],
        key=lambda item: (item["menu_item_id"], item["quantity"]),
    )
    payload = {
        "user_id": user_id,
        "delivery_address": _normalize_text(delivery_address),
        "notes": _normalize_text(notes),
        "items": normalized_items,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def serialize_menu_item(item) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
    }


def serialize_cart_item(item) -> dict[str, Any]:
    menu_item = getattr(item, "menu_item", None)
    return {
        "id": item.id,
        "menu_item_id": item.menu_item_id,
        "quantity": item.quantity,
        "menu_item": serialize_menu_item(menu_item) if menu_item else None,
    }


def serialize_cart(cart) -> dict[str, Any]:
    items = list(getattr(cart, "items", []) or [])
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "total_amount": cart.total_amount,
        "created_at": _iso(cart.created_at),
        "item_count": len(items),
        "items": [serialize_cart_item(item) for item in items],
    }


def serialize_order_item(item) -> dict[str, Any]:
    menu_item = getattr(item, "menu_item", None)
    return {
        "id": item.id,
        "menu_item_id": item.menu_item_id,
        "quantity": item.quantity,
        "menu_item": serialize_menu_item(menu_item) if menu_item else None,
    }


def serialize_order(order) -> dict[str, Any]:
    items = list(getattr(order, "items", []) or [])
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": _iso(order.created_at),
        "delivery_address": getattr(order, "delivery_address", None),
        "notes": getattr(order, "notes", None),
        "item_count": len(items),
        "items": [serialize_order_item(item) for item in items],
    }


def serialize_order_summary(order) -> dict[str, Any]:
    items = list(getattr(order, "items", []) or [])
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": _iso(order.created_at),
        "item_count": len(items),
    }


def serialize_user(user) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role_id": user.role_id,
        "role_name": getattr(user, "role_name", None),
    }


def serialize_role(role) -> dict[str, Any]:
    return {
        "id": role.id,
        "name": role.name,
    }
