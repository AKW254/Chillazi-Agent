from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.config.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)

    # Relationships
    order_items = relationship("OrderItem", back_populates="menu_item")
    cart_items = relationship("CartItem", back_populates="menu_item")