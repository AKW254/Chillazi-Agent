from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from app.config.database import Base
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime)
    total_amount = Column(Float)

    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer)

    cart = relationship("Cart", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="cart_items")
    