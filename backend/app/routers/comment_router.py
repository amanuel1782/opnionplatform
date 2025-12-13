# app/routers/comments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.models.comment_dislike import CommentDislike
from app.models.comment_report import CommentReport
from app.models.comment_share import CommentShare
from app.models.event import Event
from app.events.event_types import EventTypes

router = APIRouter(prefix="/comments", tags=["Comments"])

# ----------------------------
# EVENT LOGGER
# ----------------------------
def log_event(
    db: Session,
    actor_id: Optional[int],
    actor_role: Optional[str],
    event_type: str,
    target_type: str,
    target_id: int,
    owner_id: Optional[int] = None,
    owner_type: str = "user",
    is_anonymous: bool = False,
    metadata: Optional[dict] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None,
    source: Optional[str] = None,
    referrer: Optional[str] = None,
    app_version: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_geo: Optional[str] = None,
    latency_ms: Optional[float] = None,
):
    evt = Event(
        actor_id=actor_id,
        actor_role=actor_role,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        owner_id=owner_id,
        owner_type=owner_type,
        is_anonymous=is_anonymous,
        metadata=metadata or {},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position,
        source=source,
        referrer=referrer,
        app_version=app_version,
        ip_address=ip_address,
        user_agent=user_agent,
        user_geo=user_geo,
        latency_ms=latency_ms
    )
    db.add(evt)

# ----------------------------
# CREATE COMMENT
# ----------------------------
@router.post("/", status_code=201)
def create_comment(
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    anonymous = payload.get("anonymous", False)
    c = Comment(
        body=payload["content"],
        user_id=None if anonymous else user_id,
        target_type=payload["target_type"],
        target_id=payload["target_id"]
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_CREATED,
        target_type="comment",
        target_id=c.id,
        owner_id=c.user_id,
        is_anonymous=anonymous,
        metadata={"target_type": c.target_type, "target_id": c.target_id},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return c

# ----------------------------
# EDIT COMMENT
# ----------------------------
@router.put("/{comment_id}")
def edit_comment(
    comment_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    c = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not c:
        raise HTTPException(404, "Comment not found")
    if c.user_id and c.user_id != user_id:
        raise HTTPException(403, "Not allowed")

    changes = {}
    if "content" in payload and payload["content"] != c.body:
        changes["content"] = {"old": c.body, "new": payload["content"]}
        c.body = payload["content"]

    if "anonymous" in payload:
        old = c.user_id is None
        c.user_id = None if payload["anonymous"] else user_id
        changes["anonymous"] = {"old": old, "new": payload["anonymous"]}

    db.commit()
    db.refresh(c)

    if changes:
        log_event(
            db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.COMMENT_EDITED,
            target_type="comment",
            target_id=c.id,
            owner_id=c.user_id,
            is_anonymous=c.user_id is None,
            metadata=changes,
            session_id=session_id,
            request_id=request_id,
            feed_id=feed_id,
            position=position
        )
        db.commit()
    return c

# ----------------------------
# DELETE COMMENT (soft delete)
# ----------------------------
@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    c = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not c:
        raise HTTPException(404, "Comment not found")
    if c.user_id and c.user_id != user_id:
        raise HTTPException(403, "Not allowed")

    c.deleted_at = datetime.utcnow()
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_DELETED,
        target_type="comment",
        target_id=c.id,
        owner_id=c.user_id,
        is_anonymous=c.user_id is None,
        metadata={"target_type": c.target_type, "target_id": c.target_id},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"message": "deleted"}

# ----------------------------
# LIKE COMMENT
# ----------------------------
@router.post("/{comment_id}/like")
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    c = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not c:
        raise HTTPException(404, "Comment not found")

    if db.query(CommentLike).filter_by(comment_id=comment_id, user_id=user_id).first():
        raise HTTPException(400, "Already liked")

    db.add(CommentLike(comment_id=comment_id, user_id=user_id))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_LIKED,
        target_type="comment",
        target_id=comment_id,
        owner_id=c.user_id,
        is_anonymous=False,
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"liked": True}

# ----------------------------
# DISLIKE COMMENT
# ----------------------------
@router.post("/{comment_id}/dislike")
def dislike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    c = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not c:
        raise HTTPException(404, "Comment not found")

    if db.query(CommentDislike).filter_by(comment_id=comment_id, user_id=user_id).first():
        raise HTTPException(400, "Already disliked")

    db.add(CommentDislike(comment_id=comment_id, user_id=user_id))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_DISLIKED,
        target_type="comment",
        target_id=comment_id,
        owner_id=c.user_id,
        is_anonymous=False,
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"disliked": True}

# ----------------------------
# REPORT COMMENT
# ----------------------------
@router.post("/{comment_id}/report")
def report_comment(
    comment_id: int,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    c = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not c:
        raise HTTPException(404, "Comment not found")

    db.add(CommentReport(comment_id=comment_id, user_id=user_id, reason=reason))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_REPORTED,
        target_type="comment",
        target_id=comment_id,
        owner_id=c.user_id,
        is_anonymous=False,
        metadata={"reason": reason},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"message": "reported"}

# ----------------------------
# SHARE COMMENT
# ----------------------------
@router.post("/{comment_id}/share")
def share_comment(
    comment_id: int,
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    c = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not c:
        raise HTTPException(404, "Comment not found")

    db.add(CommentShare(comment_id=comment_id, user_id=user_id, platform=platform))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_SHARED,
        target_type="comment",
        target_id=comment_id,
        owner_id=c.user_id,
        is_anonymous=False,
        metadata={"platform": platform},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"message": "shared"}

# ----------------------------
# GET COMMENT THREAD (with nested children)
# ----------------------------
@router.get("/thread/{comment_id}")
def get_comment_thread(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    root = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at == None).first()
    if not root:
        raise HTTPException(404, "Comment not found")

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_VIEWED,
        target_type="comment",
        target_id=comment_id,
        owner_id=root.user_id,
        is_anonymous=root.user_id is None,
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()

    def build(c: Comment) -> dict:
        children = db.query(Comment).filter(
            Comment.target_type == "comment",
            Comment.target_id == c.id,
            Comment.deleted_at == None
        ).all()
        return {
            "id": c.id,
            "body": c.body,
            "user_id": c.user_id,
            "is_anonymous": c.is_anonymous,
            "created_at": c.created_at,
            "comments": [build(ch) for ch in children]
        }

    return build(root)
