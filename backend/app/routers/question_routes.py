from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.question import Question
from app.crud.crud_question import (
    toggle_question_like,
    report_question
)
from app.models.question_like import QuestionLike

router = APIRouter(prefix="/questions", tags=["Questions"])


# --------------------------
# Like / Unlike Question
# --------------------------
@router.post("/{question_id}/like")
def like_question(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    liked = toggle_question_like(db, question_id, user_id)
    likes = db.query(QuestionLike).filter(
        QuestionLike.question_id == question_id
    ).count()

    return {"liked": liked, "likes": likes}


# --------------------------
# Report Question
# --------------------------
@router.post("/{question_id}/report")
def report_question_route(
    question_id: int,
    reason: str,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    report = report_question(db, question_id, user_id, reason)
    return {"message": "Question reported", "report_id": report.id}
