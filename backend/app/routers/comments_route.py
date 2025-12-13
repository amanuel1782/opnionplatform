# routers/comments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.database import get_db
from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.models.comment_report import CommentReport
from app.models.comment_share import CommentShare
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut

router = APIRouter(prefix="/comments", tags=["Comments"])

# ----------------------------
# Create a comment (on question/answer/comment)
# ----------------------------
@router.post("/", response_model=CommentOut)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), user_id: int = 1):
    comment = Comment(**payload.dict(), user_id=user_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

# ----------------------------
# Edit a comment
# ----------------------------
@router.put("/{comment_id}", response_model=CommentOut)
def edit_comment(comment_id: int, payload: CommentUpdate, db: Session = Depends(get_db), user_id: int = 1):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        raise HTTPException(404, "Comment not found")
    if c.user_id != user_id:
        raise HTTPException(403, "You can only edit your own comments")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(c, key, value)
    db.commit()
    db.refresh(c)
    return c

# ----------------------------
# Delete a comment
# ----------------------------
@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), user_id: int = 1):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        raise HTTPException(404, "Comment not found")
    if c.user_id != user_id:
        raise HTTPException(403, "You can only delete your own comments")
    db.delete(c)
    db.commit()
    return {"message": "Comment deleted"}

# ----------------------------
# Toggle like/unlike
# ----------------------------
@router.post("/{comment_id}/like")
def toggle_like(comment_id: int, db: Session = Depends(get_db), user_id: int = 1):
    like = db.query(CommentLike).filter_by(comment_id=comment_id, user_id=user_id).first()
    if like:
        db.delete(like)
        db.commit()
        return {"liked": False}
    new_like = CommentLike(comment_id=comment_id, user_id=user_id)
    db.add(new_like)
    db.commit()
    return {"liked": True}

# ----------------------------
# Report a comment
# ----------------------------
@router.post("/{comment_id}/report")
def report_comment(comment_id: int, reason: str, db: Session = Depends(get_db), user_id: int = 1):
    report = CommentReport(comment_id=comment_id, user_id=user_id, reason=reason)
    db.add(report)
    db.commit()
    return {"message": "Reported"}

# ----------------------------
# Share a comment
# ----------------------------
@router.post("/{comment_id}/share")
def share_comment(comment_id: int, platform: str, db: Session = Depends(get_db), user_id: int = 1):
    share = CommentShare(comment_id=comment_id, user_id=user_id, platform=platform)
    db.add(share)
    db.commit()
    return {"message": f"Shared on {platform}"}

# ----------------------------
# List comments for a target (question/answer/comment) with pagination
# ----------------------------
@router.get("/")
def list_comments(target_type: str, target_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    query = db.query(Comment).filter(Comment.target_type == target_type, Comment.target_id == target_id)
    total = query.count()
    comments = query.offset((page-1)*page_size).limit(page_size).all()
    result = []
    for c in comments:
        likes_count = db.query(func.count(CommentLike.id)).filter(CommentLike.comment_id == c.id).scalar()
        reports_count = db.query(func.count(CommentReport.id)).filter(CommentReport.comment_id == c.id).scalar()
        result.append({
            "id": c.id,
            "body": c.body,
            "user_id": c.user_id,
            "is_anonymous": c.is_anonymous,
            "created_at": c.created_at,
            "likes": likes_count,
            "reports": reports_count
        })
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "comments": result
    }
# routers/comments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models import Comment
from app.models.comment_like import CommentLike
from app.models.comment_report import CommentReport
from app.models.comment_share import CommentShare
from app.schemas.cards import CommentOut

router = APIRouter(prefix="/comments", tags=["Comments"])

# ----------------------------
# Recursive helper
# ----------------------------
def get_comment_with_nested(db: Session, comment: Comment) -> dict:
    likes = db.query(func.count(CommentLike.id)).filter(CommentLike.comment_id == comment.id).scalar()
    reports = db.query(func.count(CommentReport.id)).filter(CommentReport.comment_id == comment.id).scalar()
    shares = db.query(func.count(CommentShare.id)).filter(CommentShare.comment_id == comment.id).scalar()

    nested_comments_objs = db.query(Comment).filter(Comment.target_type == "comment", Comment.target_id == comment.id).all()
    nested_comments = [get_comment_with_nested(db, c) for c in nested_comments_objs]

    return {
        "id": comment.id,
        "body": comment.body,
        "user_id": None if comment.is_anonymous else comment.user_id,
        "created_at": comment.created_at,
        "likes": likes,
        "reports": reports,
        "shares": shares,
        "comments": nested_comments
    }

# ----------------------------
# Endpoint: Get all comments for a target (question, answer, or comment)
# ----------------------------
@router.get("/{target_type}/{target_id}", response_model=List[CommentOut])
def get_comments(
    target_type: str,  # "question", "answer", "comment"
    target_id: int,
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10
):
    if target_type not in ["question", "answer", "comment"]:
        raise HTTPException(400, "Invalid target_type, must be question, answer, or comment")

    comments_query = db.query(Comment).filter(Comment.target_type == target_type, Comment.target_id == target_id)
    total_comments = comments_query.count()
    comments = comments_query.order_by(Comment.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    results = [get_comment_with_nested(db, c) for c in comments]
    return results
@router.post("/{comment_id}/dislike")
def toggle_comment_dislike(comment_id: int, db: Session = Depends(get_db), user_id: int = 1):
    from app.models.comment_dislike import CommentDislike
    existing = db.query(CommentDislike).filter(CommentDislike.comment_id==comment_id, CommentDislike.user_id==user_id).first()
    if existing:
        db.delete(existing); db.commit()
        dislikes = db.query(func.count(CommentDislike.id)).filter(CommentDislike.comment_id==comment_id).scalar()
        return {"disliked": False, "dislikes": dislikes}
    new = CommentDislike(comment_id=comment_id, user_id=user_id)
    db.add(new); db.commit()
    dislikes = db.query(func.count(CommentDislike.id)).filter(CommentDislike.comment_id==comment_id).scalar()
    return {"disliked": True, "dislikes": dislikes}
