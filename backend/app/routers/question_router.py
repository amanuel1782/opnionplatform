# app/routes/questions.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.auth_stub import get_current_user_id
from app.models.question import Question
from app.models.answer import Answer
from app.models.comment import Comment
from app.models.question_like import QuestionLike
from app.models.answer_like import AnswerLike
from app.models.report import Report
from app.models.share import Share
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.services.analytics import push_event, push_event_async
from app.services.share import generate_share_token, build_share_url

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/", status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    q = Question(
        title=payload.title,
        content=payload.content,
        anonymous=payload.anonymous,
        user_id=None if payload.anonymous else user_id
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    if background_tasks:
        background_tasks.add_task(push_event, "question.created", {"id": q.id, "user_id": user_id})
    return {"id": q.id, "created_at": q.created_at}


@router.put("/{question_id}")
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if q.user_id and q.user_id != user_id:
        raise HTTPException(403, "Not allowed")
    if payload.title is not None:
        q.title = payload.title
    if payload.content is not None:
        q.content = payload.content
    if payload.anonymous is not None:
        q.anonymous = payload.anonymous
        q.user_id = None if payload.anonymous else q.user_id
    db.commit()
    db.refresh(q)
    if background_tasks:
        background_tasks.add_task(push_event, "question.updated", {"id": question_id, "user_id": user_id})
    return {"message": "updated", "updated_at": q.updated_at}


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if q.user_id and q.user_id != user_id:
        raise HTTPException(403, "Not allowed")
    db.delete(q)
    db.commit()
    if background_tasks:
        background_tasks.add_task(push_event, "question.deleted", {"id": question_id, "user_id": user_id})
    return {"message": "deleted"}


@router.post("/{question_id}/like")
def toggle_like(question_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    ex = db.query(QuestionLike).filter(QuestionLike.question_id == question_id, QuestionLike.user_id == user_id).first()
    if ex:
        db.delete(ex); db.commit()
        likes = db.query(func.count(QuestionLike.id)).filter(QuestionLike.question_id == question_id).scalar()
        if background_tasks: background_tasks.add_task(push_event, "question.unliked", {"id": question_id, "user_id": user_id})
        return {"liked": False, "likes": likes}
    like = QuestionLike(question_id=question_id, user_id=user_id)
    db.add(like); db.commit()
    likes = db.query(func.count(QuestionLike.id)).filter(QuestionLike.question_id == question_id).scalar()
    if background_tasks: background_tasks.add_task(push_event, "question.liked", {"id": question_id, "user_id": user_id})
    return {"liked": True, "likes": likes}


@router.post("/{question_id}/report")
def report_question(question_id: int, reason: Optional[str] = Query(None, max_length=300), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    r = Report(content_type="question", content_id=question_id, reason=reason, user_id=user_id)
    db.add(r); db.commit()
    if background_tasks: background_tasks.add_task(push_event, "question.reported", {"id": question_id, "user_id": user_id})
    return {"message": "reported"}


@router.get("/{question_id}/share")
def share_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q: raise HTTPException(404, "Question not found")
    token = generate_share_token("question", question_id)
    url = build_share_url("question", question_id, token)
    # optional: persist Share model
    s = Share(entity_type="question", entity_id=question_id, token=token)
    db.add(s); db.commit()
    return {"share_url": url}


@router.get("/{question_id}/full")
def get_question_full(question_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    q = db.query(Question).options(joinedload(Question).joinedload(Question.answers)).filter(Question.id == question_id).first()
    if not q: raise HTTPException(404, "Question not found")
    total_likes = db.query(func.count(QuestionLike.id)).filter(QuestionLike.question_id == question_id).scalar()
    total_answers = db.query(func.count(Answer.id)).filter(Answer.question_id == question_id).scalar()
    answers = (
        db.query(Answer)
        .filter(Answer.question_id == question_id)
        .order_by(Answer.created_at.desc())
        .offset((page-1)*page_size)
        .limit(page_size)
        .all()
    )
    answer_ids = [a.id for a in answers] if answers else []
    # batch counts
    like_map = {}
    if answer_ids:
        rows = db.query(AnswerLike.answer_id, func.count()).filter(AnswerLike.answer_id.in_(answer_ids)).group_by(AnswerLike.answer_id).all()
        like_map = {r[0]: r[1] for r in rows}
    comment_map = {}
    if answer_ids:
        rows = db.query(func.count(Comment.id), Comment.answer_id).filter(Comment.answer_id.in_(answer_ids)).group_by(Comment.answer_id).all()
        # rows are (count, answer_id)
        comment_map = {r[1]: r[0] for r in rows}
    answers_out = []
    for a in answers:
        answers_out.append({
            "id": a.id,
            "content": a.content,
            "anonymous": a.anonymous,
            "written_by": "Anonymous" if a.anonymous else (a.user.username if a.user else None),
            "user_id": None if a.anonymous else a.user_id,
            "created_at": a.created_at,
            "likes": like_map.get(a.id, 0),
            "comments": comment_map.get(a.id, 0)
        })
    return {
        "id": q.id,
        "title": q.title,
        "content": q.content,
        "anonymous": q.anonymous,
        "asked_by": "Anonymous" if q.anonymous else (q.user.username if q.user else None),
        "user_id": None if q.anonymous else q.user_id,
        "created_at": q.created_at,
        "updated_at": q.updated_at,
        "likes": total_likes,
        "answers_total": total_answers,
        "answers_page": page,
        "answers_page_size": page_size,
        "answers": answers_out
    }
