from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.analytics_service import push_event

router = APIRouter(prefix="/comments", tags=["Comments"])


# ADD COMMENT TO QUESTION
@router.post("/question/{question_id}", status_code=201)
def add_question_comment(question_id: int, payload: CommentCreate, db: Session = Depends(get_db), user_id: int = 1):
    c = Comment(
        content=payload.content,
        question_id=question_id,
        parent_id=payload.parent_id,
        user_id=user_id if not payload.anonymous else None,
        anonymous=payload.anonymous
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    push_event("comment.created", {"comment_id": c.id})

    return {"id": c.id, "message": "Comment added"}


# ADD COMMENT TO ANSWER
@router.post("/answer/{answer_id}", status_code=201)
def add_answer_comment(answer_id: int, payload: CommentCreate, db: Session = Depends(get_db), user_id: int = 1):
    c = Comment(
        content=payload.content,
        answer_id=answer_id,
        parent_id=payload.parent_id,
        user_id=user_id if not payload.anonymous else None,
        anonymous=payload.anonymous
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    push_event("comment.created", {"comment_id": c.id})

    return {"id": c.id, "message": "Comment added"}


# EDIT COMMENT
@router.put("/{comment_id}")
def update_comment(comment_id: int, payload: CommentUpdate, db: Session = Depends(get_db)):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        raise HTTPException(404, "Comment not found")

    c.content = payload.content
    c.anonymous = payload.anonymous
    db.commit()

    push_event("comment.updated", {"comment_id": comment_id})

    return {"message": "Comment updated"}


# DELETE COMMENT
@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        raise HTTPException(404, "Comment not found")

    db.delete(c)
    db.commit()

    push_event("comment.deleted", {"comment_id": comment_id})

    return {"message": "Comment deleted"}


# LIST COMMENTS FOR QUESTION
@router.get("/question/{question_id}")
def list_question_comments(question_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.question_id == question_id).all()
    return comments


# LIST COMMENTS FOR ANSWER
@router.get("/answer/{answer_id}")
def list_answer_comments(answer_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.answer_id == answer_id).all()
    return comments
