# schemas/comment.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CommentBase(BaseModel):
    target_type: str  # "question", "answer", "comment"
    target_id: int
    body: str
    is_anonymous: Optional[bool] = False

class CommentCreate(CommentBase):
    user_id: int  # who posted

class CommentUpdate(BaseModel):
    body: Optional[str]
    is_anonymous: Optional[bool]

class CommentOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    body: str
    is_anonymous: bool
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
