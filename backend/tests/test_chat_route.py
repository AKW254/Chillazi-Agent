import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx
from openrouter.components.unauthorizedresponseerrordata import (
    UnauthorizedResponseErrorData as UnauthorizedResponseInnerData,
)
from openrouter.errors import UnauthorizedResponseError
from openrouter.errors.unauthorizedresponse_error import (
    UnauthorizedResponseErrorData,
)

import app.api.routes.chat as chat_route
from app.config.database import db_session
from app.main import app
from app.models import MenuItem
from app.models import User
from app.models.chat import ChatMessage, ChatSession
from app.schemas.user_schema import UserCreate
from app.services.order_service import OrderNotFoundError
from app.services.user_service import UserService


class _ExplodingAgent:
    def invoke(self, *_args, **_kwargs):
        raise OrderNotFoundError("User not found.")


class _UnauthorizedAgent:
    def invoke(self, *_args, **_kwargs):
        raise UnauthorizedResponseError(
            UnauthorizedResponseErrorData(
                error=UnauthorizedResponseInnerData(
                    code=401,
                    message="User not found.",
                ),
            ),
            httpx.Response(401, text="User not found."),
            "User not found.",
        )


class ChatRouteErrorHandlingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.email = f"chat-test-{uuid4().hex[:10]}@example.com"
        self.password = "debugpass123"

        with db_session() as db:
            service = UserService(db)
            service.create_user(
                UserCreate(
                    name="Chat Route Test User",
                    email=self.email,
                    password=self.password,
                )
            )
            if not db.query(MenuItem).filter(MenuItem.name == "Test Burger").first():
                db.add(
                    MenuItem(
                        name="Test Burger",
                        description="Grilled beef burger",
                        price=450.0,
                    )
                )

        login_response = self.client.post(
            "/api/users/login",
            json={"email": self.email, "password": self.password},
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self) -> None:
        with db_session() as db:
            user = db.query(User).filter(User.email == self.email).first()
            if not user:
                return

            sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
            session_ids = [session.id for session in sessions]

            if session_ids:
                db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(
                    synchronize_session=False
                )
                db.query(ChatSession).filter(ChatSession.id.in_(session_ids)).delete(
                    synchronize_session=False
                )

            db.delete(user)

    def test_chat_logs_and_maps_internal_tool_errors(self) -> None:
        with (
            patch.object(chat_route, "build_agent", return_value=_ExplodingAgent()),
            patch.object(chat_route.logger, "exception") as mocked_exception,
        ):
            response = self.client.post(
                "/api/chat",
                json={"message": "Please place my order."},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found.")
        mocked_exception.assert_called_once()

    def test_chat_uses_local_menu_fallback_when_provider_auth_fails(self) -> None:
        with patch.object(chat_route, "build_agent", return_value=_UnauthorizedAgent()):
            response = self.client.post(
                "/api/chat",
                json={"message": "Show me menu"},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("Here is the current Chillazi menu:", body["response"])
        self.assertIn("Test Burger", body["response"])
        self.assertIn("Price: 450.00", body["response"])

    def test_chat_returns_actionable_provider_error_when_no_local_fallback_exists(self) -> None:
        with patch.object(chat_route, "build_agent", return_value=_UnauthorizedAgent()):
            response = self.client.post(
                "/api/chat",
                json={"message": "Write a poem about lunch"},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "The AI chat provider rejected the request. Check OPENROUTER_API_KEY and the OpenRouter account configuration.",
        )


if __name__ == "__main__":
    unittest.main()
