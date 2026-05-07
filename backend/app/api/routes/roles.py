from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.auth import ROLE_ADMIN, require_roles
from app.config.database import get_db
from app.schemas.role_schema import RoleCreate,RoleUpdate, RoleResponse
from app.services.roles_service import RoleService

router = APIRouter()

# List roles admin only
@router.get("/", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    role_service = RoleService(db)
    return role_service.list_roles()


# Create a new role admin only
@router.post("/", response_model=RoleResponse)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    role_service = RoleService(db)
    return role_service.create_role(role)
# Get role details
@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    role_service = RoleService(db)
    role = role_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role
# Update role details admin only    
@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role: RoleUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    role_service = RoleService(db)
    updated = role_service.update_role(role_id, role)
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found")
    return updated
# Delete role admin only
@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(ROLE_ADMIN)),
):
    role_service = RoleService(db)
    ok = role_service.delete_role(role_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"detail": "Role deleted"}
