from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.api.dependencies.auth import ROLE_ADMIN, require_roles
from app.schemas.menu_schema import MenuItemCreate, MenuItemResponse
from app.services.menu_service import MenuService

router = APIRouter()
# Create a new menu item
@router.post("/", response_model=MenuItemResponse)
def create_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    menu_service = MenuService(db)
    return menu_service.create_menu_item(item)
# Get menu item details
@router.get("/{item_id}", response_model=MenuItemResponse)
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    menu_service = MenuService(db)
    menu_item = menu_service.get_menu_item(item_id)
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return menu_item
# Update menu item details
@router.put("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: int,
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    menu_service = MenuService(db)
    updated = menu_service.update_menu_item(item_id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return updated
# Delete menu item
@router.delete("/{item_id}")
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    menu_service = MenuService(db)
    ok = menu_service.delete_menu_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"detail": "Menu item deleted"}
# List all menu items
@router.get("/", response_model=list[MenuItemResponse])
def list_menu_items(db: Session = Depends(get_db)):
    menu_service = MenuService(db)
    return menu_service.list_menu_items()
