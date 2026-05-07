from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# -----------------------------
# Base
# -----------------------------
class UserBase(BaseModel):
    email: EmailStr


# -----------------------------
# Register
# -----------------------------
class UserCreate(UserBase):
    name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=8)


# -----------------------------
# Login
# -----------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# -----------------------------
# Update
# -----------------------------
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = Field(default=None, gt=0)

# -----------------------------
# Reset password
# -----------------------------
class UserResetPassword(BaseModel):
    new_password: str = Field(..., min_length=8)


# -----------------------------
# Response
# -----------------------------
class UserResponse(UserBase):
    id: int
    name: str
    role_id: int
    role_name: Optional[str] = None

    class Config:
        from_attributes = True


# -----------------------------
# Token (Auth)
# -----------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
