from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.question import QuestionOut
from app.services.question_service import (
    get_question_with_stats,
    report_question,
    share_question
)

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.get("/{question_id}", response_model=QuestionOut)
def read_question(question_id: int, db: Session = Depends(get_db)):
    data = get_question_with_stats(db, question_id)
    if not data:
        raise HTTPException(status_code=404, detail="Question not found")

    q = data["question"]
    return {
        "id": q.id,
        "title": q.title,
        "content": q.content,
        "created_at": q.created_at,
        "answers": data["answers"],
        "answer_count": data["answer_count"],
        "likes": data["likes"]
    }

@router.post("/{question_id}/report")
def report(question_id: int, reason: str, db: Session = Depends(get_db)):
    return report_question(db, question_id, reason)

@router.get("/{question_id}/share")
def share(question_id: int):
    return share_question(question_id)
