# app/schemas/question.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QuestionCreate(BaseModel):
    title: str
    content: str
    anonymous: int = 1  # 1 => anonymous, 0 => public

class QuestionUpdate(BaseModel):
    title: str
    content: str

class QuestionOut(BaseModel):
    id: int
    title: str
    content: str
    anonymous: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
