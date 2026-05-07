from __future__ import annotations

from fastapi import Depends

from app.api.dependencies.auth import (
    get_current_user as get_authenticated_user,
    get_role_name,
)
from app.models import User


def get_current_user(current_user: User = Depends(get_authenticated_user)) -> dict:
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": get_role_name(current_user),
        "role_id": current_user.role_id,
    }
