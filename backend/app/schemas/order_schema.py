from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Order status lifecycle."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderItemResponse(BaseModel):
    """Order item details."""
    id: int = Field(..., description="Order item ID")
    menu_item_id: int = Field(..., description="Menu item ID")
    quantity: int = Field(..., ge=1, description="Item quantity")
    
    class Config:
        from_attributes = True


class OrderCheckoutRequest(BaseModel):
    """Request to create order from cart."""
    user_id: Optional[int] = Field(default=None, description="Optional user ID, must match the authenticated user")
    cart_id: Optional[int] = Field(default=None, description="Optional cart ID to checkout")
    delivery_address: Optional[str] = Field(default=None, max_length=255, description="Delivery address")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Special notes/instructions")

    @model_validator(mode="after")
    def validate_checkout_target(self) -> "OrderCheckoutRequest":
        """Validate checkout target when a user ID is supplied."""
        if self.user_id is not None and self.user_id <= 0:
            raise ValueError("user_id must be a positive integer.")
        if self.cart_id is not None and self.cart_id <= 0:
            raise ValueError("cart_id must be a positive integer.")
        return self


class OrderBase(BaseModel):
    """Base order fields."""
    user_id: int = Field(..., description="User ID")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")


class OrderCreate(OrderBase):
    """Legacy: Create order directly."""
    pass


class OrderResponse(OrderBase):
    """Complete order response."""
    id: int = Field(..., description="Order ID")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    created_at: datetime = Field(..., description="Creation timestamp")
    items: List[OrderItemResponse] = Field(default_factory=list, description="Order items")
    delivery_address: Optional[str] = Field(default=None, description="Delivery address")
    notes: Optional[str] = Field(default=None, description="Order notes")

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list item response."""
    id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User ID")
    status: OrderStatus = Field(..., description="Order status")
    total_amount: float = Field(..., ge=0, description="Total amount")
    created_at: datetime = Field(..., description="Creation timestamp")
    item_count: int = Field(default=0, ge=0, description="Number of items in order")

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")


class OrderStatusUpdate(BaseModel):
    """Order status update request."""
    status: OrderStatus = Field(..., description="New status")
    reason: Optional[str] = Field(default=None, max_length=500, description="Reason for status change")

    class Config:
        from_attributes = True
