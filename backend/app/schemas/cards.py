# app/schemas/cards.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Recursive Comment schema
class CommentOut(BaseModel):
    id: int
    body: str
    user_id: Optional[int]
    created_at: datetime
    likes: int
    dislikes: int
    reports: int
    shares: int
    comments: List['CommentOut'] = []  # recursive

    class Config:
        orm_mode = True

# Answer schema
class AnswerOut(BaseModel):
    id: int
    body: str
    user_id: Optional[int]
    created_at: datetime
    likes: int
    dislikes: int
    reports: int
    shares: int
    comments_count: int
    comments: List[CommentOut]

    class Config:
        orm_mode = True

# Question schema
class QuestionCardOut(BaseModel):
    question: dict
    answers: List[AnswerOut]
    comments: List[CommentOut]
    total_answers: int
    answers_page: int
    answers_page_size: int
    total_comments: int
    comments_page: int
    comments_page_size: int
    ai_summary: Optional[str] = None

    class Config:
        orm_mode = True

# Needed for recursive Pydantic model
CommentOut.update_forward_refs()
