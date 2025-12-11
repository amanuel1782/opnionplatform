# schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    password: str  # plain text for creation, will be hashed in service

class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    profile_image: Optional[str]
    password: Optional[str]  # allow password update

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    profile_image: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
