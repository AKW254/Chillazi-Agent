import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import app.api.routes.order as order_route
from app.config.database import db_session
from app.email.renderer import TemplateRenderer
from app.models import User
from app.schemas.order_schema import OrderCheckoutRequest, OrderStatus
from app.schemas.user_schema import UserCreate
from app.services.mailer.mailer import Mailer
from app.services.order_service import OrderService
from app.services.user_service import UserService


class OrderEmailFlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.email = f"order-email-{uuid4().hex[:10]}@example.com"
        self.user_id: int | None = None

        with db_session() as db:
            service = UserService(db)
            user = service.create_user(
                UserCreate(
                    name="Order Email Test User",
                    email=self.email,
                    password="debugpass123",
                )
            )
            self.user_id = user.id

    def tearDown(self) -> None:
        with db_session() as db:
            user = db.query(User).filter_by(email=self.email).first()
            if user:
                db.delete(user)

    def test_checkout_route_constructs_order_service_with_mailer(self) -> None:
        checkout = OrderCheckoutRequest(
            delivery_address="123 Test Street",
            notes="Leave at the door",
        )
        fake_mailer = object()
        fake_service = Mock()
        fake_service.create_order_from_cart.return_value = SimpleNamespace(
            id=1,
            user_id=self.user_id,
            total_amount=10.0,
        )

        with db_session() as db:
            current_user = db.query(User).filter_by(id=self.user_id).first()
            with (
                patch.object(order_route, "create_mailer", return_value=fake_mailer),
                patch.object(order_route, "OrderService", return_value=fake_service) as mocked_service_cls,
            ):
                result = order_route.checkout_from_cart(
                    checkout=checkout,
                    db=db,
                    current_user=current_user,
                )

        self.assertEqual(result.user_id, self.user_id)
        mocked_service_cls.assert_called_once_with(db, fake_mailer)

    def test_order_service_passes_db_to_mailer_send_email(self) -> None:
        fake_mailer = Mock()
        fake_mailer.send_email.return_value = True

        order = SimpleNamespace(
            id=99,
            user_id=self.user_id,
            status=OrderStatus.PENDING.value,
            total_amount=450.0,
            delivery_address="123 Test Street",
            notes="No onions",
            items=[
                SimpleNamespace(
                    quantity=2,
                    menu_item=SimpleNamespace(name="Burger", price=225.0),
                )
            ],
        )

        with db_session() as db:
            service = OrderService(db, fake_mailer)
            service._send_order_email(order, "order_created.html", "order_created")

            fake_mailer.send_email.assert_called_once()
            kwargs = fake_mailer.send_email.call_args.kwargs
            self.assertIs(kwargs["db"], db)
            self.assertEqual(kwargs["user_id"], self.user_id)
            self.assertEqual(kwargs["template_name"], "order_created.html")

    def test_order_created_template_renders_with_dict_context(self) -> None:
        renderer = TemplateRenderer()

        html = renderer.render_template(
            "order_created.html",
            {
                "user": {"name": "Template User", "email": "template@example.com"},
                "order": {
                    "id": 77,
                    "status": "pending",
                    "total": "$24.50",
                    "items": [
                        {"name": "Burger", "quantity": 2, "price": "$12.25"},
                    ],
                    "delivery_address": "123 Test Street",
                    "notes": "Ring once",
                },
                "message_id": "msg-123",
                "tracking_url": "https://example.com/track",
            },
        )

        self.assertIn("Template User", html)
        self.assertIn("Burger", html)
        self.assertIn("#77", html)

    def test_mailer_normalizes_url_like_email_host(self) -> None:
        original_host = order_route.settings.email_host
        original_port = order_route.settings.email_port
        original_user = order_route.settings.email_user
        original_pass = order_route.settings.email_pass

        try:
            order_route.settings.email_host = "https://lim108.truehost.cloud:2083"
            order_route.settings.email_port = 587
            order_route.settings.email_user = "mailer@example.com"
            order_route.settings.email_pass = "secret"

            mailer = Mailer()
            self.assertEqual(mailer.smtp_server, "lim108.truehost.cloud")
            self.assertEqual(mailer.smtp_port, 587)
        finally:
            order_route.settings.email_host = original_host
            order_route.settings.email_port = original_port
            order_route.settings.email_user = original_user
            order_route.settings.email_pass = original_pass


if __name__ == "__main__":
    unittest.main()
