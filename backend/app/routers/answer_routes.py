# routers/answers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.database import get_db
from app.models import Answer
from app.models.answer_like import AnswerLike
from app.models.answer_report import AnswerReport
from app.models.answer_share import AnswerShare
from app.models.answer_comment import AnswerComment
from app.schemas.answer import AnswerCreate, AnswerUpdate, AnswerOut
from app.schemas.comment import CommentOut

router = APIRouter(prefix="/answers", tags=["Answers"])

# ----------------------------
# Create an answer
# ----------------------------
@router.post("/", response_model=AnswerOut)
def create_answer(payload: AnswerCreate, db: Session = Depends(get_db), user_id: int = 1):
    ans = Answer(**payload.dict(), user_id=user_id)
    db.add(ans)
    db.commit()
    db.refresh(ans)
    return ans

# ----------------------------
# Edit an answer
# ----------------------------
@router.put("/{answer_id}", response_model=AnswerOut)
def edit_answer(answer_id: int, payload: AnswerUpdate, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id).first()
    if not ans:
        raise HTTPException(404, "Answer not found")
    if ans.user_id != user_id:
        raise HTTPException(403, "You can only edit your own answers")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(ans, key, value)
    db.commit()
    db.refresh(ans)
    return ans

# ----------------------------
# Delete an answer
# ----------------------------
@router.delete("/{answer_id}")
def delete_answer(answer_id: int, db: Session = Depends(get_db), user_id: int = 1):
    ans = db.query(Answer).filter(Answer.id == answer_id).first()
    if not ans:
        raise HTTPException(404, "Answer not found")
    if ans.user_id != user_id:
        raise HTTPException(403, "You can only delete your own answers")
    db.delete(ans)
    db.commit()
    return {"message": "Answer deleted"}

# ----------------------------
# Toggle like/unlike
# ----------------------------
@router.post("/{answer_id}/like")
def toggle_like(answer_id: int, db: Session = Depends(get_db), user_id: int = 1):
    like = db.query(AnswerLike).filter_by(answer_id=answer_id, user_id=user_id).first()
    if like:
        db.delete(like)
        db.commit()
        return {"liked": False}
    new_like = AnswerLike(answer_id=answer_id, user_id=user_id)
    db.add(new_like)
    db.commit()
    return {"liked": True}

# ----------------------------
# Report an answer
# ----------------------------
@router.post("/{answer_id}/report")
def report_answer(answer_id: int, reason: str, db: Session = Depends(get_db), user_id: int = 1):
    report = AnswerReport(answer_id=answer_id, user_id=user_id, reason=reason)
    db.add(report)
    db.commit()
    return {"message": "Reported"}

# ----------------------------
# Share an answer
# ----------------------------
@router.post("/{answer_id}/share")
def share_answer(answer_id: int, platform: str, db: Session = Depends(get_db), user_id: int = 1):
    share = AnswerShare(answer_id=answer_id, user_id=user_id, platform=platform)
    db.add(share)
    db.commit()
    return {"message": f"Shared on {platform}"}

# ----------------------------
# Add a comment to an answer
# ----------------------------
@router.post("/{answer_id}/comments", response_model=CommentOut)
def add_comment(answer_id: int, body: str, is_anonymous: bool = False, db: Session = Depends(get_db), user_id: int = 1):
    comment = AnswerComment(answer_id=answer_id, user_id=user_id, content=body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

# ----------------------------
# List comments for an answer with pagination
# ----------------------------
@router.get("/{answer_id}/comments")
def list_comments(answer_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    query = db.query(AnswerComment).filter(AnswerComment.answer_id == answer_id)
    total = query.count()
    comments = query.offset((page-1)*page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "comments": [{"id": c.id, "content": c.content, "user_id": c.user_id, "created_at": c.created_at} for c in comments]
    }
from app.schemas.cards import AnswerOut, CommentOut
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models import Question, Answer, Comment
from app.models.answer_like import AnswerLike
from app.models.answer_report import AnswerReport
from app.models.answer_share import AnswerShare
from app.models.comment_like import CommentLike
from app.models.comment_report import CommentReport
from app.models.comment_share import CommentShare
from app.services.ai_summary import summarize_question_answers
from app.schemas.cards import AnswerOut, CommentOut
router = APIRouter(prefix="/answers", tags=["Answers"])

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
# Endpoint: Get all answers for a question with nested comments
# ----------------------------
@router.get("/question/{question_id}/full", response_model=List[AnswerOut])
def get_answers_with_details(
    question_id: int,
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10
):
    answers_query = db.query(Answer).filter(Answer.question_id == question_id)
    total_answers = answers_query.count()
    answers = answers_query.order_by(Answer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    answer_ids = [a.id for a in answers]

    # Fetch likes/reports/shares for answers
    answer_likes_map = dict(db.query(AnswerLike.answer_id, func.count()).filter(AnswerLike.answer_id.in_(answer_ids)).group_by(AnswerLike.answer_id).all())
    answer_reports_map = dict(db.query(AnswerReport.answer_id, func.count()).filter(AnswerReport.answer_id.in_(answer_ids)).group_by(AnswerReport.answer_id).all())
    answer_shares_map = dict(db.query(AnswerShare.answer_id, func.count()).filter(AnswerShare.answer_id.in_(answer_ids)).group_by(AnswerShare.answer_id).all())

    results = []
    for a in answers:
        # Get nested comments
        answer_comments_objs = db.query(Comment).filter(Comment.target_type == "answer", Comment.target_id == a.id).all()
        nested_comments = [get_comment_with_nested(db, c) for c in answer_comments_objs]

        results.append({
            "id": a.id,
            "body": a.body,
            "user_id": None if a.is_anonymous else a.user_id,
            "created_at": a.created_at,
            "likes": answer_likes_map.get(a.id, 0),
            "reports": answer_reports_map.get(a.id, 0),
            "shares": answer_shares_map.get(a.id, 0),
            "comments_count": len(nested_comments),
            "comments": nested_comments
        })

    return results