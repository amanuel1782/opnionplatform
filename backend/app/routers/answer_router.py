# app/routers/answers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.answer_dislike import AnswerDislike
from app.models.answer_report import AnswerReport
from app.models.answer_share import AnswerShare
from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.models.comment_dislike import CommentDislike
from app.models.comment_report import CommentReport
from app.models.comment_share import CommentShare
from app.models.event import Event
from app.events.event_types import EventTypes

router = APIRouter(prefix="/answers", tags=["Answers"])

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
# CREATE ANSWER
# ----------------------------
@router.post("/", status_code=201)
def create_answer(payload: dict, db: Session = Depends(get_db), user_id: int = 1):
    anonymous = payload.get("anonymous", False)
    ans = Answer(
        question_id=payload["question_id"],
        content=payload["content"],
        user_id=None if anonymous else user_id
    )
    db.add(ans)
    from app.models.question import Question
    db.query(Question).filter(Question.id == ans.question_id).update({
        "answers_count": Question.answers_count + 1
    })
    db.commit()
    db.refresh(ans)

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.ANSWER_CREATED,
        target_type="answer",
        target_id=ans.id,
        owner_id=ans.user_id,
        is_anonymous=anonymous,
        metadata={"question_id": ans.question_id}
    )
    db.commit()
    return ans

# ----------------------------
# EDIT ANSWER
# ----------------------------
@router.put("/{answer_id}")
def edit_answer(answer_id: int, payload: dict, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id, Answer.deleted_at == None).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")
    if ans.user_id and ans.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own answers")

    changes = {}
    if "content" in payload and payload["content"] != ans.content:
        changes["content"] = {"old": ans.content, "new": payload["content"]}
        ans.content = payload["content"]

    if "anonymous" in payload:
        old_user = ans.user_id
        ans.user_id = None if payload["anonymous"] else (ans.user_id or user_id)
        changes["anonymous"] = {"old": old_user is None, "new": payload["anonymous"]}

    db.commit()
    db.refresh(ans)

    if changes:
        log_event(
            db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.ANSWER_EDITED,
            target_type="answer",
            target_id=ans.id,
            owner_id=ans.user_id,
            is_anonymous=ans.user_id is None,
            metadata=changes
        )
        db.commit()
    return ans

# ----------------------------
# DELETE ANSWER (soft delete)
# ----------------------------
@router.delete("/{answer_id}")
def delete_answer(answer_id: int, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id, Answer.deleted_at == None).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")
    if ans.user_id and ans.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own answers")

    from app.models.question import Question
    db.query(Question).filter(Question.id == ans.question_id).update({
        "answers_count": func.greatest(Question.answers_count - 1, 0)
    })
    ans.deleted_at = datetime.utcnow()
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.ANSWER_DELETED,
        target_type="answer",
        target_id=ans.id,
        owner_id=ans.user_id,
        is_anonymous=ans.user_id is None,
        metadata={"question_id": ans.question_id, "content": ans.content}
    )
    db.commit()
    return {"message": "Answer deleted"}

# ----------------------------
# TOGGLE LIKE
# ----------------------------
@router.post("/{answer_id}/like")
def toggle_like(answer_id: int, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id, Answer.deleted_at == None).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    existing_dislike = db.query(AnswerDislike).filter_by(answer_id=answer_id, user_id=user_id).first()
    if existing_dislike:
        db.delete(existing_dislike)
        db.query(Answer).filter(Answer.id == answer_id).update({
            "dislikes_count": func.greatest(Answer.dislikes_count - 1, 0)
        })

    existing_like = db.query(AnswerLike).filter_by(answer_id=answer_id, user_id=user_id).first()
    if existing_like:
        db.delete(existing_like)
        db.query(Answer).filter(Answer.id == answer_id).update({
            "likes_count": func.greatest(Answer.likes_count - 1, 0)
        })
        db.commit()
        a = db.query(Answer).filter(Answer.id == answer_id).first()
        log_event(
            db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.ANSWER_LIKED,
            target_type="answer",
            target_id=answer_id,
            owner_id=a.user_id,
            is_anonymous=False,
            metadata={"removed": True}
        )
        db.commit()
        return {"liked": False, "likes": a.likes_count, "dislikes": a.dislikes_count}

    new_like = AnswerLike(answer_id=answer_id, user_id=user_id)
    db.add(new_like)
    db.query(Answer).filter(Answer.id == answer_id).update({
        "likes_count": Answer.likes_count + 1
    })
    db.commit()
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.ANSWER_LIKED,
        target_type="answer",
        target_id=answer_id,
        owner_id=a.user_id,
        is_anonymous=False
    )
    db.commit()
    return {"liked": True, "likes": a.likes_count, "dislikes": a.dislikes_count}

# ----------------------------
# TOGGLE DISLIKE
# ----------------------------
@router.post("/{answer_id}/dislike")
def toggle_dislike(answer_id: int, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id, Answer.deleted_at == None).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    existing_like = db.query(AnswerLike).filter_by(answer_id=answer_id, user_id=user_id).first()
    if existing_like:
        db.delete(existing_like)
        db.query(Answer).filter(Answer.id == answer_id).update({
            "likes_count": func.greatest(Answer.likes_count - 1, 0)
        })

    existing_dislike = db.query(AnswerDislike).filter_by(answer_id=answer_id, user_id=user_id).first()
    if existing_dislike:
        db.delete(existing_dislike)
        db.query(Answer).filter(Answer.id == answer_id).update({
            "dislikes_count": func.greatest(Answer.dislikes_count - 1, 0)
        })
        db.commit()
        a = db.query(Answer).filter(Answer.id == answer_id).first()
        log_event(
            db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.ANSWER_DISLIKED,
            target_type="answer",
            target_id=answer_id,
            owner_id=a.user_id,
            is_anonymous=False,
            metadata={"removed": True}
        )
        db.commit()
        return {"disliked": False, "dislikes": a.dislikes_count, "likes": a.likes_count}

    new_dis = AnswerDislike(answer_id=answer_id, user_id=user_id)
    db.add(new_dis)
    db.query(Answer).filter(Answer.id == answer_id).update({
        "dislikes_count": Answer.dislikes_count + 1
    })
    db.commit()
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.ANSWER_DISLIKED,
        target_type="answer",
        target_id=answer_id,
        owner_id=a.user_id,
        is_anonymous=False
    )
    db.commit()
    return {"disliked": True, "dislikes": a.dislikes_count, "likes": a.likes_count}

# ----------------------------
# REPORT ANSWER
# ----------------------------
@router.post("/{answer_id}/report")
def report_answer(answer_id: int, reason: str = Query(...), db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id, Answer.deleted_at == None).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    rpt = AnswerReport(answer_id=answer_id, user_id=user_id, reason=reason)
    db.add(rpt)
    db.query(Answer).filter(Answer.id == answer_id).update({
        "reports_count": Answer.reports_count + 1
    })
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.ANSWER_REPORTED,
        target_type="answer",
        target_id=answer_id,
        owner_id=ans.user_id,
        is_anonymous=False,
        metadata={"reason": reason}
    )
    db.commit()
    return {"message": "Reported"}

# ----------------------------
# SHARE ANSWER
# ----------------------------
@router.post("/{answer_id}/share")
def share_answer(answer_id: int, platform: Optional[str] = None, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id, Answer.deleted_at == None).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    sh = AnswerShare(answer_id=answer_id, user_id=user_id, platform=platform)
    db.add(sh)
    db.query(Answer).filter(Answer.id == answer_id).update({
        "shares_count": Answer.shares_count + 1
    })
    db.commit()

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.ANSWER_SHARED,
        target_type="answer",
        target_id=answer_id,
        owner_id=ans.user_id,
        is_anonymous=False,
        metadata={"platform": platform}
    )
    db.commit()
    return {"message": "Shared"}

# ----------------------------
# ADD COMMENT TO ANSWER
# ----------------------------
@router.post("/{answer_id}/comments", status_code=201)
def add_comment(answer_id: int, payload: dict, db: Session = Depends(get_db), user_id: int = 1):
    anonymous = payload.get("anonymous", False)
    comment = Comment(
        body=payload["content"],
        user_id=None if anonymous else user_id,
        target_type="answer",
        target_id=answer_id
    )
    db.add(comment)
    db.query(Answer).filter(Answer.id == answer_id).update({
        "comments_count": Answer.comments_count + 1
    })
    db.commit()
    db.refresh(comment)

    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_CREATED,
        target_type="comment",
        target_id=comment.id,
        owner_id=comment.user_id,
        is_anonymous=anonymous,
        metadata={"answer_id": answer_id}
    )
    db.commit()
    return comment

# ----------------------------
# LIST COMMENTS WITH NESTED REPLIES
# ----------------------------
def _get_comment_recursive(db: Session, comment: Comment) -> dict:
    likes = db.query(func.count(CommentLike.id)).filter(CommentLike.comment_id == comment.id).scalar()
    dislikes = db.query(func.count(CommentDislike.id)).filter(CommentDislike.comment_id == comment.id).scalar()
    reports = db.query(func.count(CommentReport.id)).filter(CommentReport.comment_id == comment.id).scalar()
    shares = db.query(func.count(CommentShare.id)).filter(CommentShare.comment_id == comment.id).scalar()
    children = db.query(Comment).filter(Comment.target_type == "comment", Comment.target_id == comment.id).all()
    return {
        "id": comment.id,
        "body": comment.body,
        "user_id": None if comment.user_id is None else comment.user_id,
        "is_anonymous": comment.is_anonymous,
        "created_at": comment.created_at,
        "likes": likes,
        "dislikes": dislikes,
        "reports": reports,
        "shares": shares,
        "comments": [_get_comment_recursive(db, ch) for ch in children]
    }

@router.get("/{answer_id}/comments")
def list_comments(answer_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db), user_id: Optional[int] = 1):
    q = db.query(Comment).filter(Comment.target_type == "answer", Comment.target_id == answer_id)
    total = q.count()
    comments = q.order_by(Comment.created_at.asc()).offset((page-1)*page_size).limit(page_size).all()

    # Log comment view event
    log_event(
        db,
        actor_id=user_id,
        actor_role="user",
        event_type=EventTypes.COMMENT_VIEWED,
        target_type="answer",
        target_id=answer_id,
        metadata={"page": page, "page_size": page_size}
    )
    db.commit()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "comments": [_get_comment_recursive(db, c) for c in comments]
    }

# ----------------------------
# GET ANSWERS WITH DETAILS
# ----------------------------
@router.get("/question/{question_id}/full")
def get_answers_with_details(
    question_id: int,
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10,
    user_id: Optional[int] = 1
):
    ans_q = db.query(Answer).filter(Answer.question_id == question_id, Answer.deleted_at == None)
    total = ans_q.count()
    answers = ans_q.order_by(Answer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    answer_ids = [a.id for a in answers]
    likes_map = dict(db.query(AnswerLike.answer_id, func.count()).filter(AnswerLike.answer_id.in_(answer_ids)).group_by(AnswerLike.answer_id).all())
    dislikes_map = dict(db.query(AnswerDislike.answer_id, func.count()).filter(AnswerDislike.answer_id.in_(answer_ids)).group_by(AnswerDislike.answer_id).all())
    reports_map = dict(db.query(AnswerReport.answer_id, func.count()).filter(AnswerReport.answer_id.in_(answer_ids)).group_by(AnswerReport.answer_id).all())
    shares_map = dict(db.query(AnswerShare.answer_id, func.count()).filter(AnswerShare.answer_id.in_(answer_ids)).group_by(AnswerShare.answer_id).all())

    results = []
    for idx, a in enumerate(answers, start=1):
        comment_objs = db.query(Comment).filter(Comment.target_type=="answer", Comment.target_id==a.id).all()
        nested = [_get_comment_recursive(db, c) for c in comment_objs]

        # Log answer viewed event per answer
        log_event(
            db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.ANSWER_VIEWED,
            target_type="answer",
            target_id=a.id,
            owner_id=a.user_id,
            is_anonymous=a.user_id is None,
            metadata={"page": page, "page_size": page_size},
            position=idx,
            feed_id="home_v1"
        )

        results.append({
            "id": a.id,
            "body": a.content,
            "user_id": None if a.user_id is None else a.user_id,
            "is_anonymous": a.is_anonymous,
            "created_at": a.created_at,
            "likes": likes_map.get(a.id, 0),
            "dislikes": dislikes_map.get(a.id, 0),
            "reports": reports_map.get(a.id, 0),
            "shares": shares_map.get(a.id, 0),
            "comments_count": len(nested),
            "comments": nested
        })

    db.commit()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "answers": results
    }
