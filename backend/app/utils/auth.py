from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.config.settings import settings


def hash_password(password: str) -> str:
	"""Hash a plaintext password using bcrypt and return the hashed string."""
	if not isinstance(password, (str, bytes)):
		raise TypeError("password must be str or bytes")
	pw = password.encode("utf-8") if isinstance(password, str) else password
	hashed = bcrypt.hashpw(pw, bcrypt.gensalt())
	return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify a plaintext password against a bcrypt hashed password."""
	if isinstance(plain_password, str):
		plain = plain_password.encode("utf-8")
	else:
		plain = plain_password
	if isinstance(hashed_password, str):
		hashed = hashed_password.encode("utf-8")
	else:
		hashed = hashed_password
	try:
		return bcrypt.checkpw(plain, hashed)
	except ValueError:
		return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
	"""Create a signed JWT containing `data` as claims.

	`data` should be a dict of claims (for example: {"sub": "user_id"}).
	"""
	to_encode = data.copy()
	now = datetime.utcnow()
	if expires_delta is None:
		expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
	expire = now + expires_delta
	to_encode.update({"iat": now, "exp": expire})
	encoded = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
	if isinstance(encoded, bytes):
		encoded = encoded.decode("utf-8")
	return encoded


def decode_access_token(token: str) -> Dict[str, Any]:
	"""Decode and verify a JWT. Raises jwt exceptions on failure."""
	return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = ["hash_password", "verify_password", "create_access_token", "decode_access_token"]