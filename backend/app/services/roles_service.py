from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Role
from app.schemas.role_schema import RoleCreate,RoleUpdate


class RoleService:
    def __init__(self, db: Session):
        self.db = db

    def create_role(self, role_in: RoleCreate) -> Role:
        role = Role(name=role_in.name)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_role(self, role_id: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_role_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()

    def list_roles(self) -> List[Role]:
        return self.db.query(Role).all()

    def update_role(self, role_id: int,  role_in: RoleUpdate) -> Optional[Role]:
        role = self.get_role(role_id)
        if not role:
            return None
        role.name = role_in.name
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role_id: int) -> bool:
        role = self.get_role(role_id)
        if not role:
            return False
        self.db.delete(role)
        self.db.commit()
        return True
