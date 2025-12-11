# app/routes/comments.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.auth_stub import get_current_user_id
from app.models.comment import Comment
from app.models.question import Question
from app.models.answer import Answer
from app.models.comment_like import CommentLike
from app.models.report import Report
from app.services.analytics import push_event
from app.schemas.comment import CommentCreate, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/question/{question_id}", status_code=201)
def add_question_comment(question_id: int, payload: CommentCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q: raise HTTPException(404, "Question not found")
    c = Comment(content=payload.content, anonymous=payload.anonymous, user_id=None if payload.anonymous else user_id, question_id=question_id, parent_id=payload.parent_id)
    db.add(c); db.commit(); db.refresh(c)
    if background_tasks: background_tasks.add_task(push_event, "comment.created", {"id": c.id, "question_id": question_id})
    return {"id": c.id, "created_at": c.created_at}


@router.post("/answer/{answer_id}", status_code=201)
def add_answer_comment(answer_id: int, payload: CommentCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a: raise HTTPException(404, "Answer not found")
    c = Comment(content=payload.content, anonymous=payload.anonymous, user_id=None if payload.anonymous else user_id, answer_id=answer_id, parent_id=payload.parent_id)
    db.add(c); db.commit(); db.refresh(c)
    if background_tasks: background_tasks.add_task(push_event, "comment.created", {"id": c.id, "answer_id": answer_id})
    return {"id": c.id, "created_at": c.created_at}


@router.put("/{comment_id}")
def update_comment(comment_id: int, payload: CommentUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c: raise HTTPException(404, "Comment not found")
    if c.user_id and c.user_id != user_id: raise HTTPException(403, "Not allowed")
    if payload.content is not None: c.content = payload.content
    if payload.anonymous is not None:
        c.anonymous = payload.anonymous
        if payload.anonymous: c.user_id = None
    db.commit(); db.refresh(c)
    if background_tasks: background_tasks.add_task(push_event, "comment.updated", {"id": comment_id})
    return {"message": "updated", "updated_at": c.updated_at}


@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c: raise HTTPException(404, "Comment not found")
    if c.user_id and c.user_id != user_id: raise HTTPException(403, "Not allowed")
    db.delete(c); db.commit()
    if background_tasks: background_tasks.add_task(push_event, "comment.deleted", {"id": comment_id})
    return {"message": "deleted"}


@router.post("/{comment_id}/like")
def like_comment(comment_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    ex = db.query(CommentLike).filter(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id).first()
    if ex:
        db.delete(ex); db.commit()
        if background_tasks: background_tasks.add_task(push_event, "comment.unliked", {"id": comment_id, "user_id": user_id})
        return {"liked": False}
    like = CommentLike(comment_id=comment_id, user_id=user_id); db.add(like); db.commit()
    if background_tasks: background_tasks.add_task(push_event, "comment.liked", {"id": comment_id, "user_id": user_id})
    return {"liked": True}


@router.post("/{comment_id}/report")
def report_comment(comment_id: int, reason: Optional[str] = Query(None, max_length=300), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), background_tasks: BackgroundTasks | None = None):
    r = Report(content_type="comment", content_id=comment_id, reason=reason, user_id=user_id)
    db.add(r); db.commit()
    if background_tasks: background_tasks.add_task(push_event, "comment.reported", {"id": comment_id, "user_id": user_id})
    return {"message": "reported"}


@router.get("/question/{question_id}")
def list_question_comments(question_id: int, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    q = db.query(Comment).filter(Comment.question_id == question_id)
    total = q.count()
    items = q.order_by(Comment.created_at.asc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "comments": items}


@router.get("/answer/{answer_id}")
def list_answer_comments(answer_id: int, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    q = db.query(Comment).filter(Comment.answer_id == answer_id)
    total = q.count()
    items = q.order_by(Comment.created_at.asc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "comments": items}
