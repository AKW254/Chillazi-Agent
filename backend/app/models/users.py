from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")
    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")
    email_logs = relationship("EmailLog", back_populates="user")

    @property
    def role_name(self):
        return self.role.name if self.role else None
