import json

from fastapi import APIRouter, Depends, HTTPException, status
from openrouter.errors import UnauthorizedResponseError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.config.database import get_db
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import ChatService
from app.services.order_service import OrderNotFoundError, OrderValidationError
from app.agents.memory import build_memory_from_db
from app.agents.agent import build_agent
from app.tools.dynamic_tools import get_tools_by_role
from app.api.dependencies.auth import get_current_user as get_auth_user, get_role_name
from app.models import User
from app.utils.logger import logger

router = APIRouter()


def _message_preview(message: str, limit: int = 200) -> str:
    normalized = " ".join(message.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _normalize_message(message: str) -> str:
    return " ".join(message.strip().lower().split())


def _is_menu_request(message: str) -> bool:
    normalized = _normalize_message(message)
    return any(keyword in normalized for keyword in ("menu", "foods", "food", "dishes", "available items"))


def _parse_tool_response(raw_result: str) -> dict | None:
    try:
        parsed = json.loads(raw_result)
    except (TypeError, json.JSONDecodeError):
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def _format_menu_items_from_tool_payload(payload: dict) -> str | None:
    if payload.get("success") is not True:
        return None

    items = payload.get("data")
    if not isinstance(items, list):
        return None

    if not items:
        return "The menu is currently empty. Please check back later for available items."

    lines = ["Here is the current Chillazi menu:"]
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or "Unnamed item"
        price = item.get("price")
        description = item.get("description")
        price_text = f"{float(price):.2f}" if isinstance(price, (int, float)) else str(price)
        detail = f" - {description}" if description else ""
        lines.append(f"{item.get('id', '?')}. {name} | Price: {price_text}{detail}")

    lines.append("If you'd like, tell me the item names and quantities you want.")
    return "\n".join(lines)


def _build_tool_based_fallback_response(message: str, tools: list) -> str | None:
    if not _is_menu_request(message):
        return None

    menu_tool = next((tool for tool in tools if getattr(tool, "name", "") == "get_menu"), None)
    if menu_tool is None:
        return None

    tool_result = menu_tool.invoke({})
    payload = _parse_tool_response(tool_result)
    if payload is None:
        return None

    return _format_menu_items_from_tool_payload(payload)


def _map_chat_exception(exc: Exception) -> tuple[int, str]:
    message = str(exc).strip()

    if isinstance(exc, UnauthorizedResponseError):
        return (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The AI chat provider rejected the request. Check OPENROUTER_API_KEY and the OpenRouter account configuration.",
        )

    if isinstance(exc, OrderNotFoundError):
        return status.HTTP_404_NOT_FOUND, message or "Requested resource was not found."

    if isinstance(exc, PermissionError):
        return status.HTTP_403_FORBIDDEN, message or "You do not have permission to perform this action."

    if isinstance(exc, OrderValidationError):
        return status.HTTP_400_BAD_REQUEST, message or "Chat request validation failed."

    if isinstance(exc, ValueError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, message or "Chat request could not be processed."

    if settings.debug:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, f"{type(exc).__name__}: {exc}"

    return status.HTTP_500_INTERNAL_SERVER_ERROR, "Chat request failed. Please try again."


@router.post("")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    auth_user: User = Depends(get_auth_user),
):
    # Build a safe dictionary with the required keys
    user = {
        "id": auth_user.id,
        "role": get_role_name(auth_user),
    }

    chat_service = ChatService(db)
    session = None
    tools = []

    try:
        # 1. Get/Create session
        session = chat_service.get_or_create_session(
            user_id=user["id"],
            session_id=req.session_id
        )

        # 2. Store user message
        chat_service.add_message(session.id, "user", req.message)

        # 3. Load recent messages
        db_messages = chat_service.get_recent_messages(session.id, limit=10)

        # 4. Convert to LLM format
        memory = build_memory_from_db(db_messages)

        # 5. Load role-based tools
        tools = get_tools_by_role(user["role"], current_user_id=user["id"])

        # 6. Build agent
        agent = build_agent(tools)

        # 7. Run agent with memory
        result = agent.invoke({
            "input": req.message,
            "chat_history": memory
        })
        if isinstance(result, dict):
            response = result.get("output") or result.get("result") or str(result)
        else:
            response = result

        # 8. Store assistant response
        chat_service.add_message(session.id, "assistant", response)

        return {
            "response": response,
            "session_id": session.id
        }

    except HTTPException as exc:
        logger.warning(
            "Chat request returned HTTP error: user_id=%s role=%s requested_session_id=%s resolved_session_id=%s detail=%s",
            user["id"],
            user["role"],
            req.session_id,
            getattr(session, "id", None),
            exc.detail,
        )
        raise
    except Exception as exc:
        if isinstance(exc, UnauthorizedResponseError):
            fallback_response = _build_tool_based_fallback_response(req.message, tools)
            if fallback_response is not None:
                logger.warning(
                    "Chat provider auth failed; served tool-based fallback: user_id=%s role=%s requested_session_id=%s resolved_session_id=%s message_preview=%r",
                    user["id"],
                    user["role"],
                    req.session_id,
                    getattr(session, "id", None),
                    _message_preview(req.message),
                )
                chat_service.add_message(session.id, "assistant", fallback_response)
                return {
                    "response": fallback_response,
                    "session_id": session.id,
                }

        error_status, error_detail = _map_chat_exception(exc)
        logger.exception(
            "Chat request failed: user_id=%s role=%s requested_session_id=%s resolved_session_id=%s message_preview=%r error_type=%s error=%s",
            user["id"],
            user["role"],
            req.session_id,
            getattr(session, "id", None),
            _message_preview(req.message),
            type(exc).__name__,
            exc,
        )
        raise HTTPException(status_code=error_status, detail=error_detail) from exc
