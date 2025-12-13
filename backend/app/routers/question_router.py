# app/routers/questions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.question import Question
from app.models.question_like import QuestionLike
from app.models.question_dislike import QuestionDislike
from app.models.question_report import QuestionReport
from app.models.question_share import QuestionShare
from app.models.answer import Answer
from app.models.comment import Comment
from app.models.event import Event
from app.events.event_types import EventTypes

router = APIRouter(prefix="/questions", tags=["Questions"])

# ----------------------------
# Generic Event Logger
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
# CREATE QUESTION
# ----------------------------
@router.post("/", status_code=201)
def create_question(
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    anonymous = payload.get("anonymous", False)
    q = Question(
        title=payload["title"],
        content=payload.get("content", ""),
        user_id=None if anonymous else user_id
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_CREATED,
        target_type="question",
        target_id=q.id,
        owner_id=q.user_id,
        is_anonymous=anonymous,
        metadata={"title": q.title},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"id": q.id, "created_at": q.created_at}

# ----------------------------
# UPDATE QUESTION
# ----------------------------
@router.put("/{question_id}")
def update_question(
    question_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if q.user_id and q.user_id != user_id:
        raise HTTPException(403, "Not allowed")

    changes = {}
    if "title" in payload and payload["title"] != q.title:
        changes["title"] = {"old": q.title, "new": payload["title"]}
        q.title = payload["title"]
    if "content" in payload and payload["content"] != q.content:
        changes["content"] = {"old": q.content, "new": payload["content"]}
        q.content = payload["content"]
    if "anonymous" in payload:
        old = q.user_id is None
        q.user_id = None if payload["anonymous"] else user_id
        changes["anonymous"] = {"old": old, "new": payload["anonymous"]}

    db.commit()
    db.refresh(q)

    if changes:
        log_event(
            db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.QUESTION_EDITED,
            target_type="question",
            target_id=q.id,
            owner_id=q.user_id,
            is_anonymous=q.user_id is None,
            metadata=changes,
            session_id=session_id,
            request_id=request_id,
            feed_id=feed_id,
            position=position
        )
        db.commit()

    return {"message": "updated", "updated_at": q.updated_at}

# ----------------------------
# DELETE QUESTION (soft delete)
# ----------------------------
@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if q.user_id and q.user_id != user_id:
        raise HTTPException(403, "Not allowed")

    q.deleted_at = datetime.utcnow()
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_DELETED,
        target_type="question",
        target_id=q.id,
        owner_id=q.user_id,
        is_anonymous=q.user_id is None,
        metadata={"title": q.title},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"message": "deleted"}

# ----------------------------
# LIKE QUESTION
# ----------------------------
@router.post("/{question_id}/like")
def like_question(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if db.query(QuestionLike).filter_by(question_id=question_id, user_id=user_id).first():
        raise HTTPException(400, "Already liked")

    db.add(QuestionLike(question_id=question_id, user_id=user_id))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_LIKED,
        target_type="question",
        target_id=question_id,
        owner_id=q.user_id,
        is_anonymous=False,
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"liked": True}

# ----------------------------
# DISLIKE QUESTION
# ----------------------------
@router.post("/{question_id}/dislike")
def dislike_question(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if db.query(QuestionDislike).filter_by(question_id=question_id, user_id=user_id).first():
        raise HTTPException(400, "Already disliked")

    db.add(QuestionDislike(question_id=question_id, user_id=user_id))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_DISLIKED,
        target_type="question",
        target_id=question_id,
        owner_id=q.user_id,
        is_anonymous=False,
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()
    return {"disliked": True}

# ----------------------------
# REPORT QUESTION
# ----------------------------
@router.post("/{question_id}/report")
def report_question(
    question_id: int,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")

    db.add(QuestionReport(question_id=question_id, user_id=user_id, reason=reason))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_REPORTED,
        target_type="question",
        target_id=question_id,
        owner_id=q.user_id,
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
# SHARE QUESTION
# ----------------------------
@router.post("/{question_id}/share")
def share_question(
    question_id: int,
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = 1,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")

    db.add(QuestionShare(question_id=question_id, user_id=user_id, platform=platform))
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_SHARED,
        target_type="question",
        target_id=question_id,
        owner_id=q.user_id,
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
# Recursive comments helper with engagement metrics
# ----------------------------
def _get_comment_recursive(db: Session, comment: Comment) -> dict:
    children = db.query(Comment).filter(
        Comment.target_type == "comment",
        Comment.target_id == comment.id,
        Comment.deleted_at == None
    ).all()

    # Engagement metrics per comment
    comment_events = db.query(Event).filter(Event.target_type == "comment", Event.target_id == comment.id).all()
    comment_engagement_metrics = {
        "total_events": len(comment_events),
        "likes_events": len([e for e in comment_events if e.event_type == EventTypes.COMMENT_LIKED]),
        "dislikes_events": len([e for e in comment_events if e.event_type == EventTypes.COMMENT_DISLIKED]),
        "reports_events": len([e for e in comment_events if e.event_type == EventTypes.COMMENT_REPORTED]),
        "shares_events": len([e for e in comment_events if e.event_type == EventTypes.COMMENT_SHARED])
    }

    return {
        "id": comment.id,
        "body": comment.body,
        "user_id": comment.user_id,
        "is_anonymous": comment.user_id is None,
        "created_at": comment.created_at,
        "engagement_metrics": comment_engagement_metrics,
        "comments": [_get_comment_recursive(db, ch) for ch in children]
    }

# ----------------------------
# GET QUESTION CARD (full view)
# ----------------------------
@router.get("/{question_id}/full")
def get_question_card(
    question_id: int,
    db: Session = Depends(get_db),
    answers_page: int = 1,
    answers_page_size: int = 10,
    comments_page: int = 1,
    comments_page_size: int = 10,
    include_ai_summary: bool = False,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    feed_id: Optional[str] = None,
    position: Optional[int] = None
):
    # Fetch question
    q = db.query(Question).filter(Question.id == question_id, Question.deleted_at == None).first()
    if not q:
        raise HTTPException(404, "Question not found")

    # ----------------------------
    # Log VIEW event for question
    # ----------------------------
    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.QUESTION_VIEWED,
        target_type="question",
        target_id=q.id,
        owner_id=q.user_id,
        is_anonymous=q.user_id is None,
        metadata={"answers_page": answers_page, "answers_page_size": answers_page_size},
        session_id=session_id,
        request_id=request_id,
        feed_id=feed_id,
        position=position
    )
    db.commit()

    # ----------------------------
    # Question engagement metrics
    # ----------------------------
    question_events = db.query(Event).filter(Event.target_type == "question", Event.target_id == question_id).all()
    question_engagement_metrics = {
        "total_events": len(question_events),
        "likes_events": len([e for e in question_events if e.event_type == EventTypes.QUESTION_LIKED]),
        "dislikes_events": len([e for e in question_events if e.event_type == EventTypes.QUESTION_DISLIKED]),
        "reports_events": len([e for e in question_events if e.event_type == EventTypes.QUESTION_REPORTED]),
        "shares_events": len([e for e in question_events if e.event_type == EventTypes.QUESTION_SHARED]),
        "answers_events": len([e for e in question_events if e.event_type == EventTypes.ANSWER_CREATED]),
        "comments_events": len([e for e in question_events if e.event_type.startswith("comment_")])
    }

    # ----------------------------
    # Paginated answers
    # ----------------------------
    ans_q = db.query(Answer).filter(Answer.question_id == question_id, Answer.deleted_at == None)
    total_answers = ans_q.count()
    answers = ans_q.order_by(Answer.created_at.desc()).offset((answers_page-1)*answers_page_size).limit(answers_page_size).all()
    answer_ids = [a.id for a in answers]

    # Engagement metrics for answers
    from app.models.answer_like import AnswerLike
    from app.models.answer_dislike import AnswerDislike
    from app.models.answer_report import AnswerReport
    from app.models.answer_share import AnswerShare

    likes_map = dict(db.query(AnswerLike.answer_id, func.count()).filter(AnswerLike.answer_id.in_(answer_ids)).group_by(AnswerLike.answer_id).all())
    dislikes_map = dict(db.query(AnswerDislike.answer_id, func.count()).filter(AnswerDislike.answer_id.in_(answer_ids)).group_by(AnswerDislike.answer_id).all())
    reports_map = dict(db.query(AnswerReport.answer_id, func.count()).filter(AnswerReport.answer_id.in_(answer_ids)).group_by(AnswerReport.answer_id).all())
    shares_map = dict(db.query(AnswerShare.answer_id, func.count()).filter(AnswerShare.answer_id.in_(answer_ids)).group_by(AnswerShare.answer_id).all())

    answers_data = []
    for a in answers:
        answer_comments = db.query(Comment).filter(Comment.target_type == "answer", Comment.target_id == a.id, Comment.deleted_at == None).all()
        nested_comments = [_get_comment_recursive(db, c) for c in answer_comments]

        # Answer events
        answer_events = db.query(Event).filter(Event.target_type == "answer", Event.target_id == a.id).all()
        answer_engagement_metrics = {
            "total_events": len(answer_events),
            "likes_events": len([e for e in answer_events if e.event_type == EventTypes.ANSWER_LIKED]),
            "dislikes_events": len([e for e in answer_events if e.event_type == EventTypes.ANSWER_DISLIKED]),
            "reports_events": len([e for e in answer_events if e.event_type == EventTypes.ANSWER_REPORTED]),
            "shares_events": len([e for e in answer_events if e.event_type == EventTypes.ANSWER_SHARED]),
            "comments_events": len([e for e in answer_events if e.event_type.startswith("comment_")])
        }

        answers_data.append({
            "id": a.id,
            "body": a.content,
            "user_id": None if a.user_id is None else a.user_id,
            "is_anonymous": a.user_id is None,
            "created_at": a.created_at,
            "likes": likes_map.get(a.id, 0),
            "dislikes": dislikes_map.get(a.id, 0),
            "reports": reports_map.get(a.id, 0),
            "shares": shares_map.get(a.id, 0),
            "comments_count": len(nested_comments),
            "comments": nested_comments,
            "engagement_metrics": answer_engagement_metrics
        })

    # ----------------------------
    # Paginated question comments
    # ----------------------------
    question_comments_q = db.query(Comment).filter(Comment.target_type == "question", Comment.target_id == question_id, Comment.deleted_at == None)
    total_q_comments = question_comments_q.count()
    q_comments = question_comments_q.order_by(Comment.created_at.asc()).offset((comments_page-1)*comments_page_size).limit(comments_page_size).all()
    comments_data = [_get_comment_recursive(db, c) for c in q_comments]

    return {
        "question": {
            "id": q.id,
            "title": q.title,
            "body": q.content,
            "user_id": None if q.user_id is None else q.user_id,
            "is_anonymous": q.user_id is None,
            "created_at": q.created_at,
            "engagement_metrics": question_engagement_metrics
        },
        "answers": answers_data,
        "comments": comments_data,
        "total_answers": total_answers,
        "answers_page": answers_page,
        "answers_page_size": answers_page_size,
        "total_comments": total_q_comments,
        "comments_page": comments_page,
        "comments_page_size": comments_page_size
    }

