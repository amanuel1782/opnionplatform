from pydantic import BaseModel
from datetime import datetime

class AnswerBase(BaseModel):
    content: str
    anonymous: int

class AnswerOut(BaseModel):
    id: int
    content: str
    anonymous: int
    user_id: int | None
    created_at: datetime

    class Config:
        orm_mode = True
