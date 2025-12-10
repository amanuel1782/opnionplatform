from pydantic import BaseModel
from datetime import datetime

class AnswerCreate(BaseModel):
    content: str
    anonymous: int

class AnswerOut(BaseModel):
    id: int
    content: str
    anonymous: int
    created_at: datetime
    written_by: str | None
    likes: int
    comments: int

    class Config:
        orm_mode = True
