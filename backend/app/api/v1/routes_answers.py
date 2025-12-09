from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.answer import AnswerCreate, AnswerOut
from app.models.answer import Answer
from app.db.database import get_db

router = APIRouter()

@router.post("/", response_model=AnswerOut)
def create_answer(data: AnswerCreate, db: Session = Depends(get_db)):
    a = Answer(question_id=data.question_id, content=data.content, user_id=1)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
