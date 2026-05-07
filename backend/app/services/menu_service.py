from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import MenuItem
from app.schemas.menu_schema import MenuItemCreate


class MenuService:
    def __init__(self, db: Session):
        self.db = db

    def create_menu_item(self, item_in: MenuItemCreate) -> MenuItem:
        item = MenuItem(name=item_in.name, description=item_in.description, price=item_in.price)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_menu_item(self, item_id: int) -> Optional[MenuItem]:
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def list_menu_items(self) -> List[MenuItem]:
        return self.db.query(MenuItem).all()

    def update_menu_item(self, item_id: int, item_in: MenuItemCreate) -> Optional[MenuItem]:
        item = self.get_menu_item(item_id)
        if not item:
            return None
        item.name = item_in.name
        item.description = item_in.description
        item.price = item_in.price
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_menu_item(self, item_id: int) -> bool:
        item = self.get_menu_item(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True
