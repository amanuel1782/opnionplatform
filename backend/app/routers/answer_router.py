from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.report import Report
from app.schemas.answer import AnswerCreate, AnswerUpdate
from app.services.analytics_service import push_event

router = APIRouter(prefix="/answers", tags=["Answers"])


@router.post("/question/{question_id}", status_code=201)
def add_answer(question_id: int, payload: AnswerCreate, db: Session = Depends(get_db), user_id: int = 1):
    a = Answer(
        content=payload.content,
        question_id=question_id,
        user_id=user_id if not payload.anonymous else None,
        anonymous=payload.anonymous
    )
    db.add(a)
    db.commit()
    db.refresh(a)

    push_event("answer.created", {"answer_id": a.id})

    return {"id": a.id, "message": "Answer added"}


@router.put("/{answer_id}")
def update_answer(answer_id: int, payload: AnswerUpdate, db: Session = Depends(get_db)):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a:
        raise HTTPException(404, "Answer not found")

    a.content = payload.content
    db.commit()

    push_event("answer.updated", {"answer_id": answer_id})

    return {"message": "Answer updated"}


@router.delete("/{answer_id}")
def delete_answer(answer_id: int, db: Session = Depends(get_db)):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a:
        raise HTTPException(404, "Answer not found")

    db.delete(a)
    db.commit()

    push_event("answer.deleted", {"answer_id": answer_id})

    return {"message": "Answer deleted"}


# LIKE / UNLIKE
@router.post("/{answer_id}/like")
def like_answer(answer_id: int, db: Session = Depends(get_db), user_id: int = 1):
    exists = db.query(AnswerLike).filter(
        AnswerLike.answer_id == answer_id,
        AnswerLike.user_id == user_id
    ).first()

    if exists:
        db.delete(exists)
        db.commit()
        return {"liked": False, "likes": count_answer_likes(db, answer_id)}

    like = AnswerLike(answer_id=answer_id, user_id=user_id)
    db.add(like)
    db.commit()

    return {"liked": True, "likes": count_answer_likes(db, answer_id)}


def count_answer_likes(db, answer_id):
    return db.query(AnswerLike).filter(AnswerLike.answer_id == answer_id).count()


# REPORT
@router.post("/{answer_id}/report")
def report_answer(answer_id: int, reason: str, db: Session = Depends(get_db), user_id: int = 1):
    report = Report(
        content_type="answer",
        content_id=answer_id,
        reason=reason,
        user_id=user_id
    )
    db.add(report)
    db.commit()
    return {"message": "Reported successfully"}
