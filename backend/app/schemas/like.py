# schemas/like.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LikeBase(BaseModel):
    target_type: str  # "question", "answer", "comment"
    target_id: int

class LikeCreate(LikeBase):
    user_id: int  # who liked

class LikeOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
