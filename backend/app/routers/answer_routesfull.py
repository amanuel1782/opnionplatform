from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.answer import Answer
from app.schemas.answer import AnswerCreate
from app.services.ai_summary import summarize_question_answers
router = APIRouter(prefix="/answers", tags=["Answers"])


@router.put("/{answer_id}")
def edit_answer(
    answer_id: int,
    payload: AnswerCreate,
    db: Session = Depends(get_db),
    user_id: int = 1     # Replace with auth
):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()

    if not answer:
        raise HTTPException(404, "Answer not found")

    if answer.user_id != user_id:
        raise HTTPException(403, "You can only edit your own answers")

    answer.content = payload.content
    answer.anonymous = payload.anonymous
    db.commit()
    db.refresh(answer)

    return {"message": "Answer updated", "answer_id": answer.id}
@router.delete("/{answer_id}")
def delete_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()

    if not answer:
        raise HTTPException(404, "Answer not found")

    if answer.user_id != user_id:
        raise HTTPException(403, "You can only delete your own answers")

    db.delete(answer)
    db.commit()

    return {"message": "Answer deleted"}

@router.get("/question/{question_id}/paginated")
def get_paginated_answers(
    question_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Answer).filter(Answer.question_id == question_id)
    total = query.count()

    answers = query.order_by(Answer.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "answers": answers
    }
@router.get("/{question_id}/ai-summary")
def ai_answer_feed(
    question_id: int,
    db: Session = Depends(get_db)
):
    summary = summarize_question_answers(db, question_id)
    return {"summary": summary}

