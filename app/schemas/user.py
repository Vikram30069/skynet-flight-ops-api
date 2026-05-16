from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.models import Role

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: Role
    base_id: str | None = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
