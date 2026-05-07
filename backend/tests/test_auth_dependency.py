import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config.database import db_session
from app.main import app
from app.models import User
from app.schemas.user_schema import UserCreate
from app.services.user_service import UserService


class AuthDependencyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.email = f"auth-test-{uuid4().hex[:10]}@example.com"
        self.password = "debugpass123"
        self.user_id: int | None = None

        with db_session() as db:
            service = UserService(db)
            user = service.create_user(
                UserCreate(
                    name="Auth Test User",
                    email=self.email,
                    password=self.password,
                )
            )
            self.user_id = user.id

    def tearDown(self) -> None:
        with db_session() as db:
            user = db.query(User).filter(User.email == self.email).first()
            if user:
                db.delete(user)

    def test_deleted_user_token_requires_relogin(self) -> None:
        login_response = self.client.post(
            "/api/users/login",
            json={"email": self.email, "password": self.password},
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me_response = self.client.get("/api/users/me", headers=headers)
        self.assertEqual(me_response.status_code, 200)

        with db_session() as db:
            user = db.query(User).filter(User.id == self.user_id).first()
            if user:
                db.delete(user)

        expired_user_response = self.client.get("/api/users/me", headers=headers)
        self.assertEqual(expired_user_response.status_code, 401)
        self.assertEqual(
            expired_user_response.json()["detail"],
            "User for this token was not found. Please sign in again.",
        )


if __name__ == "__main__":
    unittest.main()
