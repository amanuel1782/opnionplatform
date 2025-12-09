from pydantic import BaseModel

class AnswerCreate(BaseModel):
    question_id: int
    content: str

class AnswerOut(BaseModel):
    id: int
    question_id: int
    content: str
    user_id: int

    class Config:
        orm_mode = True
