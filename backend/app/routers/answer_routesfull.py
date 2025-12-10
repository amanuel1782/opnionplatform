from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.answer_comment import AnswerComment
from app.schemas.answer import AnswerCreate
from app.services.ai_summary import summarize_question_answers
from app.services.data_dispatcher import dispatch_answer_to_services

router = APIRouter(prefix="/answers", tags=["Answers"])


# -------------------------------------------------------------
# EDIT ANSWER
# -------------------------------------------------------------
@router.put("/{answer_id}")
def edit_answer(
    answer_id: int,
    payload: AnswerCreate,
    db: Session = Depends(get_db),
    user_id: int = 1   # TODO: replace with auth system
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


# -------------------------------------------------------------
# DELETE ANSWER
# -------------------------------------------------------------
@router.delete("/{answer_id}")
def delete_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,  # TODO: replace with auth
):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()

    if not answer:
        raise HTTPException(404, "Answer not found")

    if answer.user_id != user_id:
        raise HTTPException(403, "You can only delete your own answers")

    db.delete(answer)
    db.commit()

    return {"message": "Answer deleted"}


# -------------------------------------------------------------
# PAGINATED ANSWERS
# -------------------------------------------------------------
@router.get("/question/{question_id}")
def get_paginated_answers(
    question_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Answer).filter(Answer.question_id == question_id)
    total = query.count()

    answers = (
        query.order_by(Answer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for a in answers:
        likes = db.query(AnswerLike).filter(AnswerLike.answer_id == a.id).count()
        comments = db.query(AnswerComment).filter(AnswerComment.answer_id == a.id).count()

        results.append({
            "id": a.id,
            "content": a.content,
            "anonymous": a.anonymous,
            "user_id": None if a.anonymous else a.user_id,
            "created_at": a.created_at,
            "likes": likes,
            "comments": comments
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "answers": results
    }


# -------------------------------------------------------------
# AI SUMMARY OF ANSWERS
# -------------------------------------------------------------
@router.get("/{question_id}/ai-summary")
def ai_answer_feed(
    question_id: int,
    db: Session = Depends(get_db)
):
    summary = summarize_question_answers(db, question_id)
    return {"summary": summary}
