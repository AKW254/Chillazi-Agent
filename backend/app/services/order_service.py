from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from app.models import Order, OrderItem, Cart, CartItem, User
from app.schemas.order_schema import OrderCreate, OrderStatus
from app.services.cart_service import CartService
from app.services.mailer.mailer import Mailer
from app.tools._shared import build_order_signature
from app.utils.logger import logger


class OrderServiceError(Exception):
    """Base exception for order service failures."""


class OrderNotFoundError(OrderServiceError):
    """Raised when an order or cart target cannot be found."""


class OrderValidationError(OrderServiceError):
    """Raised when business rules prevent an order action."""


class OrderService:
    def __init__(self, db: Session, mailer: Optional[Mailer] = None):
        self.db = db
        self.mailer = mailer

    def _get_user_email_and_context(self, order: Order) -> tuple[str, dict]:
        """Get user email and prepare email context for the order."""
        user = self.db.query(User).filter(User.id == order.user_id).first()
        if not user:
            raise OrderNotFoundError(f"User not found for order {order.id}")

        # Prepare order items with names and prices
        order_items = []
        for item in order.items:
            if item.menu_item:
                order_items.append({
                    'name': item.menu_item.name,
                    'quantity': item.quantity,
                    'price': f"${item.menu_item.price:.2f}"
                })

        context = {
            'user': {
                'name': user.name,
                'email': user.email
            },
            'order': {
                'id': order.id,
                'status': order.status,
                'total': f"${order.total_amount:.2f}",
                'items': order_items,
                'delivery_address': order.delivery_address,
                'notes': order.notes
            }
        }
        return user.email, context

    def _send_order_email(self, order: Order, template_name: str, event_type: str) -> None:
        """Send email for order event if mailer is configured."""
        if not self.mailer:
            logger.debug(f"Mailer not configured, skipping email for order {order.id}")
            return

        try:
            to_email, context = self._get_user_email_and_context(order)
            context['event_type'] = event_type
            subject = f"Order #{order.id} - {event_type.replace('_', ' ').title()}"

            success = self.mailer.send_email(
                to_email=to_email,
                subject=subject,
                template_name=template_name,
                context=context,
                user_id=order.user_id,
                db=self.db,
            )
            if success:
                logger.info(f"Email sent for order {order.id}: {event_type}")
            else:
                logger.warning(f"Failed to send email for order {order.id}: {event_type}")
        except Exception as e:
            logger.error(f"Error sending email for order {order.id}: {type(e).__name__}: {str(e)}")

    def _get_cart_for_checkout(
        self,
        *,
        cart_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Cart:
        """Resolve the cart used for checkout and validate ownership."""
        query = self.db.query(Cart).options(
            selectinload(Cart.items).selectinload(CartItem.menu_item)
        )

        cart: Optional[Cart] = None
        if cart_id is not None:
            logger.debug(f"Querying cart by ID: {cart_id}")
            cart = query.filter(Cart.id == cart_id).first()
        elif user_id is not None:
            logger.debug(f"Querying cart by user_id: {user_id}")
            cart = query.filter(Cart.user_id == user_id).first()

        if not cart:
            logger.warning(f"Cart not found: cart_id={cart_id}, user_id={user_id}")
            raise OrderNotFoundError("Cart not found")

        if user_id is not None and cart.user_id != user_id:
            logger.warning(f"Cart ownership mismatch: cart.user_id={cart.user_id}, provided user_id={user_id}")
            raise OrderValidationError("The selected cart does not belong to the provided user")

        if not cart.items:
            logger.warning(f"Cart is empty: cart_id={cart.id}, user_id={cart.user_id}")
            raise OrderValidationError("Cart is empty")

        missing_menu_items = [item.menu_item_id for item in cart.items if item.menu_item is None]
        if missing_menu_items:
            logger.warning(f"Cart contains unavailable menu items: {missing_menu_items}")
            raise OrderValidationError("Cart contains unavailable menu items")

        return cart

    def _ensure_user_exists(self, user_id: int) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            raise OrderNotFoundError("User not found")
        logger.debug(f"User verified to exist: user_id={user_id}")

    def _find_recent_similar_order(
        self,
        *,
        user_id: int,
        cart: Cart,
        delivery_address: Optional[str],
        notes: Optional[str],
        lookback_minutes: int,
    ) -> Optional[Order]:
        cutoff = datetime.utcnow() - timedelta(minutes=lookback_minutes)
        target_signature = build_order_signature(
            user_id,
            cart.items,
            delivery_address=delivery_address,
            notes=notes,
        )

        recent_orders = (
            self.db.query(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.menu_item))
            .filter(Order.user_id == user_id, Order.created_at >= cutoff)
            .order_by(Order.created_at.desc())
            .all()
        )

        for existing_order in recent_orders:
            existing_signature = build_order_signature(
                existing_order.user_id,
                existing_order.items,
                delivery_address=existing_order.delivery_address,
                notes=existing_order.notes,
            )
            if existing_signature == target_signature:
                logger.warning(
                    "Duplicate checkout detected: user_id=%s, order_id=%s, window_minutes=%s",
                    user_id,
                    existing_order.id,
                    lookback_minutes,
                )
                return existing_order

        return None

    def create_order_from_cart(
        self, 
        *,
        cart_id: Optional[int] = None,
        user_id: Optional[int] = None,
        delivery_address: Optional[str] = None,
        notes: Optional[str] = None,
        clear_cart: bool = True,
        dedupe_window_minutes: int = 5,
    ) -> Order:
        """Create order from cart items (modern checkout pattern)."""
        try:
            logger.debug(f"Creating order from cart: cart_id={cart_id}, user_id={user_id}")
            
            cart = self._get_cart_for_checkout(cart_id=cart_id, user_id=user_id)
            logger.debug(f"Cart retrieved: cart_id={cart.id}, user_id={cart.user_id}, items={len(cart.items)}")
            
            self._ensure_user_exists(cart.user_id)
            logger.debug(f"User verified: user_id={cart.user_id}")

            if dedupe_window_minutes > 0:
                existing_order = self._find_recent_similar_order(
                    user_id=cart.user_id,
                    cart=cart,
                    delivery_address=delivery_address,
                    notes=notes,
                    lookback_minutes=dedupe_window_minutes,
                )
                if existing_order:
                    setattr(existing_order, "_duplicate_checkout", True)
                    setattr(existing_order, "_duplicate_checkout_window_minutes", dedupe_window_minutes)
                    if clear_cart:
                        CartService(self.db).clear_cart(cart.id)
                    logger.info(
                        "Returning existing order instead of creating duplicate: user_id=%s, order_id=%s",
                        cart.user_id,
                        existing_order.id,
                    )
                    return existing_order

            order_total = round(
                sum(item.menu_item.price * item.quantity for item in cart.items),
                2,
            )
            logger.debug(f"Order total calculated: {order_total}")

            order = Order(
                user_id=cart.user_id,
                status=OrderStatus.PENDING.value,
                delivery_address=delivery_address,
                notes=notes,
                total_amount=order_total,
            )
            self.db.add(order)
            self.db.flush()
            logger.debug(f"Order created and flushed: order_id={order.id}")

            for cart_item in cart.items:
                self.db.add(
                    OrderItem(
                        order_id=order.id,
                        menu_item_id=cart_item.menu_item_id,
                        quantity=cart_item.quantity,
                    )
                )
            logger.debug(f"Order items added: {len(cart.items)} items")

            if clear_cart:
                for cart_item in list(cart.items):
                    self.db.delete(cart_item)
                cart.total_amount = 0.0
                logger.debug("Cart items cleared")

            self.db.commit()
            logger.debug(f"Transaction committed: order_id={order.id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Rollback due to error: {type(e).__name__}: {str(e)}")
            raise

        created_order = self.get_order(order.id)
        if not created_order:
            logger.error(f"Order was created but could not be reloaded: order_id={order.id}")
            raise OrderNotFoundError("Order was created but could not be reloaded")

        # Send confirmation email
        self._send_order_email(created_order, "order_created.html", "order_created")

        logger.info(f"Order created successfully: order_id={created_order.id}, total={created_order.total_amount}")
        return created_order


    def get_order(self, order_id: int) -> Optional[Order]:
        """Get order with items loaded."""
        return self.db.query(Order).options(
            selectinload(Order.items).selectinload(OrderItem.menu_item)
        ).filter(Order.id == order_id).first()

    def list_orders(self, user_id: Optional[int] = None, skip: int = 0, limit: Optional[int] = None) -> List[Order]:
        """
        List orders with pagination.
        
        Args:
            user_id: Filter by user (optional)
            skip: Number of items to skip
            limit: Max items to return
        """
        query = self.db.query(Order).options(selectinload(Order.items))
        
        if user_id is not None:
            logger.debug(f"Filtering orders by user_id: {user_id}")
            query = query.filter(Order.user_id == user_id)
            
        query = query.order_by(Order.created_at.desc())
        
        if skip > 0:
            query = query.offset(skip)
            
        if limit is not None:
            query = query.limit(limit)
            
        results = query.all()
        logger.debug(f"Retrieved {len(results)} orders (user_id={user_id}, skip={skip}, limit={limit})")
        return results
    def cancel_order(
        self,
        order_id: int,
        user_id: int,
        reason: Optional[str] = None,
    ) -> Optional[Order]:
        """Cancel a user's order when it is still actionable."""
        order = self.get_order(order_id)
        if not order:
            logger.warning(f"Order not found for cancellation: order_id={order_id}")
            return None
        if order.user_id != user_id:
            logger.warning(f"User {user_id} attempted to cancel order {order_id} owned by user {order.user_id}")
            raise OrderValidationError("You do not have permission to cancel this order")
        normalized_status = str(order.status).strip().lower()

        if normalized_status == OrderStatus.CANCELLED.value:
            setattr(order, "_already_cancelled", True)
            logger.info(
                "Order already cancelled: order_id=%s, user_id=%s, reason=%s",
                order_id,
                user_id,
                reason,
            )
            return order

        cancellable_statuses = {
            OrderStatus.PENDING.value,
            OrderStatus.CONFIRMED.value,
        }
        if normalized_status not in cancellable_statuses:
            logger.warning(f"Order {order_id} cannot be canceled due to status: {order.status}")
            raise OrderValidationError("Only pending or confirmed orders can be cancelled")

        order.status = OrderStatus.CANCELLED.value
        try:
            self.db.commit()
            self.db.refresh(order)
            logger.info(
                "Order status changed: order_id=%s, user_id=%s, status=%s, reason=%s",
                order_id,
                user_id,
                order.status,
                reason,
            )

            # Send cancellation email
            self._send_order_email(order, "order_cancelled.html", "order_cancelled")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cancel order: order_id={order_id}, user_id={user_id}, error={type(e).__name__}: {str(e)}")
            raise
        return self.get_order(order.id) or order
    

    def update_order_status(self, order_id: int, status: OrderStatus, reason: Optional[str] = None) -> Optional[Order]:
        """
        Update order status with optional audit reason.
        
        Args:
            order_id: Order to update
            status: New status
            reason: Optional reason for change (audit trail)
            
        Returns:
            Updated order or None if not found
        """
        order = self.get_order(order_id)
        if not order:
            logger.warning(f"Order not found for status update: order_id={order_id}")
            return None
            
        old_status = order.status
        order.status = status.value

        try:
            self.db.commit()
            logger.info(f"Order status changed: order_id={order_id}, {old_status} -> {status.value}, reason={reason}")

            # Send status update email for important status changes
            important_statuses = {OrderStatus.CONFIRMED.value, OrderStatus.PREPARING.value, OrderStatus.READY.value, OrderStatus.COMPLETED.value}
            if status.value in important_statuses:
                self._send_order_email(order, "order_status_update.html", f"order_{status.value.lower()}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update order status: order_id={order_id}, {str(e)}")
            raise

        return self.get_order(order_id)

    def delete_order(self, order_id: int) -> bool:
        """Delete order (cascades to items)."""
        order = self.get_order(order_id)
        if not order:
            return False
        self.db.delete(order)
        self.db.commit()
        return True
