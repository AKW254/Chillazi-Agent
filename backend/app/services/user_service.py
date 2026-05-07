from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from app.models import User, Role
from app.schemas.user_schema import UserCreate,UserLogin,UserUpdate
from app.utils.auth import hash_password, verify_password, create_access_token


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def _user_query(self):
        return self.db.query(User).options(selectinload(User.role))

    def create_user(self, user_in: UserCreate, user_id: Optional[int] = None) -> User:
        # Ensure a default "user" role exists
        role = self.db.query(Role).filter(Role.name == "user").first()
        if not role:
            role = Role(name="user")
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)

        pw_hash = hash_password(user_in.password)
        user = User(name=user_in.name, email=user_in.email, password_hash=pw_hash, role_id=role.id)
        if user_id is not None:
            user.id = user_id
            self.db.add(user)
            self.db.commit()
            # For explicit id, we need to refresh differently or just return
            self.db.refresh(user)
        else:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def authenticate_user(self, user_in: UserLogin) -> dict:
        user = self.db.query(User).filter(User.email == user_in.email).first()
        if not user or not verify_password(user_in.password, user.password_hash):
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
             )

        role_name = user.role.name if user.role else None
        token = create_access_token({"sub": str(user.id), "role": role_name})

        return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": role_name,
        }
    }

    def get_user(self, user_id: int) -> Optional[User]:
        return self._user_query().filter(User.id == user_id).first()

    def list_users(self) -> list[User]:
        return self._user_query().order_by(User.id.asc()).all()

    def update_user(self, user_id: int, user_in: UserUpdate) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None
        if user_in.name is not None:
            user.name = user_in.name
        if user_in.email is not None:
            user.email = user_in.email
        if user_in.role_id is not None:
            role = self.db.query(Role).filter(Role.id == user_in.role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found",
                )
            user.role_id = role.id
        self.db.commit()
        self.db.refresh(user)
        return self.get_user(user_id)

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def reset_password(self, user_id: int, new_password: str) -> bool:
        user = self.get_user(user_id)

        if not user:
            return False

        user.password_hash = hash_password(new_password)
        self.db.commit()

        return True
