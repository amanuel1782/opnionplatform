# schemas/report.py
from pydantic import BaseModel
from datetime import datetime

class ReportBase(BaseModel):
    target_type: str  # "question", "answer", "comment"
    target_id: int
    reason: str

class ReportCreate(ReportBase):
    user_id: int  # who reported

class ReportOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    reason: str
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
