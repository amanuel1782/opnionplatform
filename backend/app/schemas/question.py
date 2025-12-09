from pydantic import BaseModel

class QuestionCreate(BaseModel):
    content: str

class QuestionOut(BaseModel):
    id: int
    content: str
    user_id: int

    class Config:
        orm_mode = True
