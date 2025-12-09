from pydantic import BaseModel
from datetime import datetime
from typing import List
from .answer import AnswerOut

class QuestionOut(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    answers: List[AnswerOut]
    answer_count: int
    likes: int

    class Config:
        orm_mode = True
