from pydantic import BaseModel
from datetime import datetime
from typing import List
from .answer import AnswerOut
from .user import UserOut

class QuestionOut(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    anonymous: int
    user: UserOut
    answers: List[AnswerOut]
    like_count: int
    answer_count: int
    share_url: str

    class Config:
        orm_mode = True
