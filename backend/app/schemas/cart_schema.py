from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class MenuItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float

class CartItemBase(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdateQuantity(BaseModel):
     quantity: int = Field(..., gt=0)

class CartItemResponse(CartItemBase):
    id: int
    menu_item: MenuItemBase

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    created_at: datetime
    items: List[CartItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
