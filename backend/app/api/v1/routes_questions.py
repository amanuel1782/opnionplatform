from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.question import QuestionCreate, QuestionOut
from app.models.question import Question
from app.db.database import get_db

router = APIRouter()

@router.post("/", response_model=QuestionOut)
def create_question(data: QuestionCreate, db: Session = Depends(get_db)):
    q = Question(content=data.content, user_id=1)  # temporary: user_id=1 for now
    db.add(q)
    db.commit()
    db.refresh(q)
    return q
