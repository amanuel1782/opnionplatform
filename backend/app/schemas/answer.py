# app/schemas/answer.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnswerCreate(BaseModel):
    content: str
    anonymous: Optional[bool] = False

class AnswerUpdate(BaseModel):
    content: Optional[str] = None
    anonymous: Optional[bool] = None

class AnswerOut(BaseModel):
    id: int
    question_id: int
    content: str
    anonymous: bool
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
