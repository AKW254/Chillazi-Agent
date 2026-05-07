from __future__ import annotations

from typing import Callable, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, selectinload

from app.config.database import get_db
from app.models import User
from app.utils.auth import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)

ROLE_GUEST = "guest"
ROLE_USER = "user"
ROLE_ADMIN = "admin"


# -----------------------------
# Exceptions
# -----------------------------
def _unauthorized_exception(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# -----------------------------
# Role utilities
# -----------------------------
def get_role_name(user: User) -> str:
    if user.role and user.role.name:
        return user.role.name.lower()
    return ROLE_GUEST


def _user_query(db: Session):
    return db.query(User).options(selectinload(User.role))


def _get_user_from_subject(db: Session, subject: object) -> Optional[User]:
    if isinstance(subject, int) or (isinstance(subject, str) and subject.isdigit()):
        return _user_query(db).filter(User.id == int(subject)).first()

    if isinstance(subject, str):
        return _user_query(db).filter(User.email == subject).first()

    return None


# -----------------------------
# Core resolver
# -----------------------------
def _resolve_user_from_credentials(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: Session,
    *,
    required: bool,
) -> Optional[User]:

    if credentials is None:
        if required:
            raise _unauthorized_exception("Authentication required")
        return None

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise _unauthorized_exception("Invalid or expired token") from exc

    subject = payload.get("sub")

    if subject is None:
        raise _unauthorized_exception("Invalid token: missing subject")

    # -----------------------------
    # Resolve user
    # -----------------------------
    user = _get_user_from_subject(db, subject)

    if not user:
        raise _unauthorized_exception("User for this token was not found. Please sign in again.")

    return user


# -----------------------------
# Dependencies
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    return _resolve_user_from_credentials(credentials, db, required=True)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    return _resolve_user_from_credentials(credentials, db, required=False)


# -----------------------------
# RBAC
# -----------------------------
def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    normalized_roles = {r.lower() for r in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        role = get_role_name(current_user)

        if role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Allowed roles: {', '.join(sorted(normalized_roles))}",
            )

        return current_user

    return dependency


# -----------------------------
# Ownership
# -----------------------------
def ensure_self_or_admin(current_user: User, target_user_id: int) -> None:
    if current_user.id == target_user_id or get_role_name(current_user) == ROLE_ADMIN:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only access your own resources",
    )
