from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
