from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models import User
from app.api.dependencies.auth import ROLE_ADMIN
from app.schemas.user_schema import UserCreate,UserLogin,UserUpdate,UserResetPassword,UserResponse
from app.services.user_service import UserService
from app.api.dependencies.auth import ensure_self_or_admin, get_current_user, require_roles

router = APIRouter()

# Create a new user
@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)
    try:
        return user_service.create_user(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Authenticate user (login)
@router.post("/login")
def authenticate_user(user: UserLogin, db: Session = Depends(get_db)):
    user_service = UserService(db)
    try:
        return user_service.authenticate_user(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(ROLE_ADMIN)),
):
    user_service = UserService(db)
    try:
        return user_service.list_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


# Get user details
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, user_id)
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Update user details
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, user_id)
    if user.role_id is not None and current_user.role_name != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    user_service = UserService(db)
    try:
        updated = user_service.update_user(user_id, user)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete user
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, user_id)
    user_service = UserService(db)
    ok = user_service.delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}


#Reset user password
@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    user: UserResetPassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, user_id)
    user_service = UserService(db)

    ok = user_service.reset_password(user_id, user.new_password)

    if not ok:
        raise HTTPException(status_code=404, detail="User not found")

    return {"detail": "Password reset"}
