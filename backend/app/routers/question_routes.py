# routers/questions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.database import get_db
from app.models import Question, Answer
from app.models.question_like import QuestionLike
from app.models.question_report import QuestionReport
from app.models.question_share import QuestionShare
from app.models.answer import Answer
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionOut
from app.schemas.answer import AnswerOut
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models import Question, Answer, Comment
from app.models.question_like import QuestionLike
from app.models.question_report import QuestionReport
from app.models.question_share import QuestionShare
from app.models.answer_like import AnswerLike
from app.models.answer_report import AnswerReport
from app.models.answer_share import AnswerShare
from app.models.answer_comment import AnswerComment
from app.models.comment_like import CommentLike
from app.models.comment_report import CommentReport
from app.models.comment_share import CommentShare
from app.services.ai_summary import summarize_question_answers
router = APIRouter(prefix="/questions", tags=["Questions"])

# ----------------------------
# Create a question
# ----------------------------
@router.post("/", response_model=QuestionOut)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db), user_id: int = 1):
    q = Question(**payload.dict(), created_by=user_id)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

# ----------------------------
# Edit a question
# ----------------------------
@router.put("/{question_id}", response_model=QuestionOut)
def edit_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db), user_id: int = 1):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if q.created_by != user_id:
        raise HTTPException(403, "You can only edit your own questions")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(q, key, value)
    db.commit()
    db.refresh(q)
    return q

# ----------------------------
# Delete a question
# ----------------------------
@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), user_id: int = 1):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    if q.created_by != user_id:
        raise HTTPException(403, "You can only delete your own questions")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted"}

# ----------------------------
# Toggle like/unlike
# ----------------------------
@router.post("/{question_id}/like")
def toggle_like(question_id: int, db: Session = Depends(get_db), user_id: int = 1):
    like = db.query(QuestionLike).filter_by(question_id=question_id, user_id=user_id).first()
    if like:
        db.delete(like)
        db.commit()
        return {"liked": False}
    new_like = QuestionLike(question_id=question_id, user_id=user_id)
    db.add(new_like)
    db.commit()
    return {"liked": True}

# ----------------------------
# Report a question
# ----------------------------
@router.post("/{question_id}/report")
def report_question(question_id: int, reason: str, db: Session = Depends(get_db), user_id: int = 1):
    report = QuestionReport(question_id=question_id, user_id=user_id, reason=reason)
    db.add(report)
    db.commit()
    return {"message": "Reported"}

# ----------------------------
# Share a question
# ----------------------------
@router.post("/{question_id}/share")
def share_question(question_id: int, platform: str, db: Session = Depends(get_db), user_id: int = 1):
    share = QuestionShare(question_id=question_id, user_id=user_id, platform=platform)
    db.add(share)
    db.commit()
    return {"message": f"Shared on {platform}"}

# ----------------------------
# List question with answers + stats
# ----------------------------
@router.get("/{question_id}/full")
def get_full_question(question_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")

    # Stats
    likes = db.query(func.count(QuestionLike.id)).filter(QuestionLike.question_id == question_id).scalar()
    reports = db.query(func.count(QuestionReport.id)).filter(QuestionReport.question_id == question_id).scalar()
    shares = db.query(func.count(QuestionShare.id)).filter(QuestionShare.question_id == question_id).scalar()

    # Paginated answers
    answers = db.query(Answer).filter(Answer.question_id == question_id)\
        .offset((page-1)*page_size).limit(page_size).all()

    return {
        "id": q.id,
        "title": q.title,
        "body": q.body,
        "created_by": q.created_by,
        "likes": likes,
        "reports": reports,
        "shares": shares,
        "answers_total": db.query(Answer).filter(Answer.question_id==question_id).count(),
        "answers_page": page,
        "answers_page_size": page_size,
        "answers": [{"id": a.id, "body": a.body, "created_by": a.created_by, "is_anonymous": a.is_anonymous} for a in answers]
    }
router = APIRouter(prefix="/cards", tags=["Cards"])

# ----------------------------
# Recursive helper
# ----------------------------
def get_comment_with_nested(db: Session, comment: Comment) -> dict:
    """Return a comment with its nested comments recursively."""
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
# Main Endpoint
# ----------------------------
@router.get("/question/{question_id}")
def get_question_card(
    question_id: int,
    db: Session = Depends(get_db),
    answers_page: int = 1,
    answers_page_size: int = 10,
    comments_page: int = 1,
    comments_page_size: int = 10,
    include_ai_summary: bool = False
):
    # ----------------------------
    # Fetch question
    # ----------------------------
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    # ----------------------------
    # Question stats
    # ----------------------------
    question_likes = db.query(func.count(QuestionLike.id)).filter(QuestionLike.question_id == question_id).scalar()
    question_reports = db.query(func.count(QuestionReport.id)).filter(QuestionReport.question_id == question_id).scalar()
    question_shares = db.query(func.count(QuestionShare.id)).filter(QuestionShare.question_id == question_id).scalar()

    # ----------------------------
    # Paginated answers
    # ----------------------------
    answers_query = db.query(Answer).filter(Answer.question_id == question_id)
    total_answers = answers_query.count()
    answers = answers_query.offset((answers_page-1)*answers_page_size).limit(answers_page_size).all()
    answer_ids = [a.id for a in answers]

    # Fetch answer stats
    answer_likes_map = dict(db.query(AnswerLike.answer_id, func.count()).filter(AnswerLike.answer_id.in_(answer_ids)).group_by(AnswerLike.answer_id).all())
    answer_reports_map = dict(db.query(AnswerReport.answer_id, func.count()).filter(AnswerReport.answer_id.in_(answer_ids)).group_by(AnswerReport.answer_id).all())
    answer_shares_map = dict(db.query(AnswerShare.answer_id, func.count()).filter(AnswerShare.answer_id.in_(answer_ids)).group_by(AnswerShare.answer_id).all())

    # Fetch nested comments for answers
    answers_data = []
    for a in answers:
        answer_comments_objs = db.query(Comment).filter(Comment.target_type == "answer", Comment.target_id == a.id).all()
        nested_comments = [get_comment_with_nested(db, c) for c in answer_comments_objs]

        answers_data.append({
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

    # ----------------------------
    # Paginated comments on question
    # ----------------------------
    question_comments_query = db.query(Comment).filter(Comment.target_type == "question", Comment.target_id == question_id)
    total_comments = question_comments_query.count()
    question_comments = question_comments_query.offset((comments_page-1)*comments_page_size).limit(comments_page_size).all()
    comments_data = [get_comment_with_nested(db, c) for c in question_comments]

    # ----------------------------
    # Optional AI summary
    # ----------------------------
    ai_summary = None
    if include_ai_summary and answers:
        ai_summary = summarize_question_answers(db, question_id)

    # ----------------------------
    # Final Response
    # ----------------------------
    return {
        "question": {
            "id": question.id,
            "title": question.title,
            "body": question.body,
            "user_id": question.user_id,
            "created_at": question.created_at,
            "likes": question_likes,
            "reports": question_reports,
            "shares": question_shares,
            "is_anonymous": question.is_anonymous
        },
        "answers": answers_data,
        "comments": comments_data,
        "total_answers": total_answers,
        "answers_page": answers_page,
        "answers_page_size": answers_page_size,
        "total_comments": total_comments,
        "comments_page": comments_page,
        "comments_page_size": comments_page_size,
        "ai_summary": ai_summary
    }