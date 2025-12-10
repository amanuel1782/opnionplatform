from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.db.database import get_db
from app.models.question import Question
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.answer_comment import AnswerComment
from app.models.question_like import QuestionLike

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("/{question_id}/full")
def get_full_question(
    question_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    q = (
        db.query(Question)
        .options(joinedload(Question.user))  # load author
        .filter(Question.id == question_id)
        .first()
    )

    if not q:
        raise HTTPException(404, "Question not found")

    # ---- Question stats ----
    total_likes = db.query(func.count(QuestionLike.id)).filter(
        QuestionLike.question_id == question_id
    ).scalar()

    total_answers = db.query(func.count(Answer.id)).filter(
        Answer.question_id == question_id
    ).scalar()

    # ---- Paginated answers ----
    answers = (
        db.query(Answer)
        .options(joinedload(Answer.user))
        .filter(Answer.question_id == question_id)
        .order_by(Answer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    answer_ids = [a.id for a in answers]

    # ---- Batch fetch likes & comments counts ----
    like_map = dict(
        db.query(AnswerLike.answer_id, func.count())
        .filter(AnswerLike.answer_id.in_(answer_ids))
        .group_by(AnswerLike.answer_id)
        .all()
    )

    comment_map = dict(
        db.query(AnswerComment.answer_id, func.count())
        .filter(AnswerComment.answer_id.in_(answer_ids))
        .group_by(AnswerComment.answer_id)
        .all()
    )

    answer_list = []
    for a in answers:
        answer_list.append({
            "id": a.id,
            "content": a.content,
            "anonymous": a.anonymous,
            "written_by": "Anonymous" if a.anonymous else a.user.username,
            "created_at": a.created_at,
            "likes": like_map.get(a.id, 0),
            "comments": comment_map.get(a.id, 0)
        })

    return {
        "id": q.id,
        "title": q.title,
        "content": q.content,
        "created_at": q.created_at,
        "asked_by": q.user.username if q.user else None,
        "likes": total_likes,
        "answers_total": total_answers,
        "answers_page": page,
        "answers_page_size": page_size,
        "answers": answer_list,
    }
