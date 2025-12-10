from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.question import Question
from app.models.question_like import QuestionLike
from app.models.report import Report
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.services.analytics_service import push_event

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/", status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db), user_id: int = 1):
    q = Question(
        title=payload.title,
        content=payload.content,
        user_id=user_id if not payload.anonymous else None,
        anonymous=payload.anonymous
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    push_event("question.created", {"question_id": q.id})

    return {"id": q.id, "message": "Question created"}


@router.put("/{question_id}")
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")

    q.title = payload.title
    q.content = payload.content
    db.commit()

    push_event("question.updated", {"question_id": question_id})

    return {"message": "Question updated"}


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")

    db.delete(q)
    db.commit()

    push_event("question.deleted", {"question_id": question_id})

    return {"message": "Question deleted"}


# -------------------
# LIKE / UNLIKE
# -------------------

@router.post("/{question_id}/like")
def like_question(question_id: int, db: Session = Depends(get_db), user_id: int = 1):
    exists = db.query(QuestionLike).filter(
        QuestionLike.question_id == question_id,
        QuestionLike.user_id == user_id
    ).first()

    if exists:
        db.delete(exists)
        db.commit()
        return {"liked": False, "likes": count_likes(db, question_id)}

    like = QuestionLike(question_id=question_id, user_id=user_id)
    db.add(like)
    db.commit()

    return {"liked": True, "likes": count_likes(db, question_id)}


def count_likes(db, question_id):
    return db.query(QuestionLike).filter(QuestionLike.question_id == question_id).count()


# -------------------
# REPORT
# -------------------

@router.post("/{question_id}/report")
def report_question(question_id: int, reason: str, db: Session = Depends(get_db), user_id: int = 1):
    report = Report(
        content_type="question",
        content_id=question_id,
        reason=reason,
        user_id=user_id
    )
    db.add(report)
    db.commit()
    return {"message": "Reported successfully"}


# -------------------
# GET DETAILS
# -------------------

@router.get("/{question_id}")
def get_full_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")

    answer_count = db.query(Answer).filter(Answer.question_id == question_id).count()
    likes = count_likes(db, question_id)

    return {
        "id": q.id,
        "title": q.title,
        "content": q.content,
        "user_id": None if q.anonymous else q.user_id,
        "created_at": q.created_at,
        "likes": likes,
        "answers": answer_count
    }
