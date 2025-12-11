# schemas/share.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ShareBase(BaseModel):
    target_type: str  # "question", "answer", "comment"
    target_id: int
    platform: Optional[str] = None  # e.g., "facebook", "telegram"

class ShareCreate(ShareBase):
    user_id: int  # who shared

class ShareOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    platform: Optional[str]
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
