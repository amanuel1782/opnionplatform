# app/routes/answers.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.auth_stub import get_current_user_id
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.comment import Comment
from app.models.report import Report
from app.models.share import Share
from app.services.analytics_service import push_event
from app.services.share import generate_share_token, build_share_url
from app.schemas.answer import AnswerCreate, AnswerUpdate

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("/question/{question_id}", status_code=201)
def add_answer(question_id: int, payload: AnswerCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    a = Answer(question_id=question_id, content=payload.content, anonymous=payload.anonymous, user_id=None if payload.anonymous else user_id)
    db.add(a); db.commit(); db.refresh(a)
    if background_tasks: background_tasks.add_task(push_event, "answer.created", {"id": a.id, "question_id": question_id, "user_id": user_id})
    return {"id": a.id, "created_at": a.created_at}


@router.put("/{answer_id}")
def update_answer(answer_id: int, payload: AnswerUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a: raise HTTPException(404, "Answer not found")
    if a.user_id and a.user_id != user_id: raise HTTPException(403, "Not allowed")
    if payload.content is not None: a.content = payload.content
    if payload.anonymous is not None:
        a.anonymous = payload.anonymous
        if payload.anonymous: a.user_id = None
    db.commit(); db.refresh(a)
    if background_tasks: background_tasks.add_task(push_event, "answer.updated", {"id": answer_id, "user_id": user_id})
    return {"message": "updated", "updated_at": a.updated_at}


@router.delete("/{answer_id}")
def delete_answer(answer_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a: raise HTTPException(404, "Answer not found")
    if a.user_id and a.user_id != user_id: raise HTTPException(403, "Not allowed")
    db.delete(a); db.commit()
    if background_tasks: background_tasks.add_task(push_event, "answer.deleted", {"id": answer_id, "user_id": user_id})
    return {"message": "deleted"}


@router.post("/{answer_id}/like")
def toggle_like(answer_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    ex = db.query(AnswerLike).filter(AnswerLike.answer_id == answer_id, AnswerLike.user_id == user_id).first()
    if ex:
        db.delete(ex); db.commit()
        c = db.query(func.count(AnswerLike.id)).filter(AnswerLike.answer_id == answer_id).scalar()
        if background_tasks: background_tasks.add_task(push_event, "answer.unliked", {"id": answer_id, "user_id": user_id})
        return {"liked": False, "likes": c}
    like = AnswerLike(answer_id=answer_id, user_id=user_id); db.add(like); db.commit()
    c = db.query(func.count(AnswerLike.id)).filter(AnswerLike.answer_id == answer_id).scalar()
    if background_tasks: background_tasks.add_task(push_event, "answer.liked", {"id": answer_id, "user_id": user_id})
    return {"liked": True, "likes": c}


@router.post("/{answer_id}/report")
def report_answer(answer_id: int, reason: Optional[str] = Query(None, max_length=300), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    r = Report(content_type="answer", content_id=answer_id, reason=reason, user_id=user_id)
    db.add(r); db.commit()
    if background_tasks: background_tasks.add_task(push_event, "answer.reported", {"id": answer_id, "user_id": user_id})
    return {"message": "reported"}


@router.get("/{answer_id}/share")
def share_answer(answer_id: int, db: Session = Depends(get_db)):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a: raise HTTPException(404, "Answer not found")
    token = generate_share_token("answer", answer_id)
    url = build_share_url("answer", answer_id, token)
    s = Share(entity_type="answer", entity_id=answer_id, token=token)
    db.add(s); db.commit()
    return {"share_url": url}


@router.get("/question/{question_id}")
def list_answers(question_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    q = db.query(Answer).filter(Answer.question_id == question_id)
    total = q.count()
    items = q.order_by(Answer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    results = []
    for a in items:
        likes = db.query(func.count(AnswerLike.id)).filter(AnswerLike.answer_id == a.id).scalar()
        comments = db.query(func.count(Comment.id)).filter(Comment.answer_id == a.id).scalar()
        results.append({
            "id": a.id,
            "content": a.content,
            "anonymous": a.anonymous,
            "user_id": None if a.anonymous else a.user_id,
            "created_at": a.created_at,
            "likes": likes,
            "comments": comments
        })
    return {"total": total, "page": page, "page_size": page_size, "answers": results}
