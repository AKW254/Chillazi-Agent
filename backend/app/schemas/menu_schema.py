from pydantic import BaseModel

class MenuItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemResponse(MenuItemBase):
    id: int

    class Config:
        from_attributes = True