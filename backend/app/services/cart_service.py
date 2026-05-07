from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
from app.models import Cart, CartItem, MenuItem
from app.schemas.cart_schema import CartItemCreate


class CartService:
    def __init__(self, db: Session):
        self.db = db

    def _cart_query(self):
        return self.db.query(Cart).options(
            selectinload(Cart.items).selectinload(CartItem.menu_item)
        )

    def _calculate_total(self, cart: Cart) -> float:
        """Calculate cart total from items."""
        total = sum(item.menu_item.price * item.quantity for item in cart.items)
        return round(total, 2)

    def get_cart(self, cart_id: int) -> Optional[Cart]:
        """Get cart by ID with items loaded, or None if not found."""
        cart = self._cart_query().filter(Cart.id == cart_id).first()
        if cart:
            cart.total_amount = self._calculate_total(cart)
        return cart

    def get_or_create_cart(self, user_id: int) -> Cart:
        """Get existing cart or create new one."""
        cart = self._cart_query().filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id, created_at=datetime.utcnow(), total_amount=0.0)
            self.db.add(cart)
            self.db.commit()
            cart = self.get_cart(cart.id)
         
        # Update total from items
        cart.total_amount = self._calculate_total(cart)
        self.db.commit()
        self.db.refresh(cart)
        return cart

    def get_cart_by_user(self, user_id: int) -> Optional[Cart]:
        """Get cart for user with items, or None if not found."""
        cart = self._cart_query().filter(Cart.user_id == user_id).first()
        if cart:
            cart.total_amount = self._calculate_total(cart)
        return cart

    def list_carts(self, user_id: int | None = None) -> list[Cart]:
        """List carts with totals recalculated."""
        query = self._cart_query().order_by(Cart.created_at.desc(), Cart.id.desc())
        if user_id is not None:
            query = query.filter(Cart.user_id == user_id)

        carts = query.all()
        for cart in carts:
            cart.total_amount = self._calculate_total(cart)
        return carts

    def create_cart(self, user_id: int) -> Cart:
        """Create new cart for user."""
        now = datetime.utcnow()
        cart = Cart(user_id=user_id, created_at=now, total_amount=0.0)
        self.db.add(cart)
        self.db.commit()
        self.db.refresh(cart)
        return cart

    def add_item_to_cart(self, cart_id: int, item_in: CartItemCreate) -> Optional[CartItem]:
        """Add or update item in cart."""
        cart = self._cart_query().filter(Cart.id == cart_id).first()
        if not cart:
            return None

        # Check if menu item exists
        menu_item = self.db.query(MenuItem).filter(MenuItem.id == item_in.menu_item_id).first()
        if not menu_item:
            return None

        # Check if item already in cart
        existing = self.db.query(CartItem).filter(
            CartItem.cart_id == cart_id,
            CartItem.menu_item_id == item_in.menu_item_id
        ).first()

        if existing:
            existing.quantity += item_in.quantity
            self.db.commit()
            self.db.refresh(existing)
            item = existing
        else:
            item = CartItem(cart_id=cart_id, menu_item_id=item_in.menu_item_id, quantity=item_in.quantity)
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)

        # Update cart total
        cart.total_amount = self._calculate_total(cart)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item_from_cart(self, cart_id: int, menu_item_id: int) -> bool:
        """Remove item from cart."""
        item = self.db.query(CartItem).filter(
            CartItem.cart_id == cart_id,
            CartItem.menu_item_id == menu_item_id
        ).first()
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()

        # Update cart total
        cart = self.get_cart(cart_id)
        if cart:
            cart.total_amount = self._calculate_total(cart)
            self.db.commit()
        return True

    def update_item_quantity(self, cart_id: int, menu_item_id: int, quantity: int) -> Optional[CartItem]:
        """Update item quantity in cart."""
        if quantity <= 0:
            return None

        item = self.db.query(CartItem).filter(
            CartItem.cart_id == cart_id,
            CartItem.menu_item_id == menu_item_id
        ).first()
        if not item:
            return None

        item.quantity = quantity
        self.db.commit()
        self.db.refresh(item)

        # Update cart total
        cart = self.get_cart(cart_id)
        if cart:
            cart.total_amount = self._calculate_total(cart)
            self.db.commit()
        return item

    def clear_cart(self, cart_id: int) -> bool:
        """Remove all items from cart."""
        cart = self.get_cart(cart_id)
        if not cart:
            return False

        items = self.db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
        for item in items:
            self.db.delete(item)
        self.db.commit()

        cart.total_amount = 0.0
        self.db.commit()
        return True

    def delete_cart(self, cart_id: int) -> bool:
        """Delete entire cart and items."""
        cart = self.get_cart(cart_id)
        if not cart:
            return False
        self.db.delete(cart)
        self.db.commit()
        return True
