from app.models.answer_like import AnswerLike
from app.models.answer_comment import AnswerComment
from app.models.answer import Answer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.question import Question
from app.models.question_like import QuestionLike
from app.models.answer import Answer
from app.services.ai_summary import summarize_question_answers

router = APIRouter()
@router.get("/question/{question_id}")
def get_answers(question_id: int, db: Session = Depends(get_db)):
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()

    results = []
    for a in answers:
        likes_count = (
            db.query(AnswerLike)
            .filter(AnswerLike.answer_id == a.id)
            .count()
        )

        comments_count = (
            db.query(AnswerComment)
            .filter(AnswerComment.answer_id == a.id)
            .count()
        )

        results.append({
            "id": a.id,
            "content": a.content,
            "anonymous": a.anonymous,
            "written_by": "Anonymous" if a.anonymous == 1 else a.user.username,
            "user_id": None if a.anonymous else a.user_id,
            "created_at": a.created_at,
            "likes": likes_count,
            "comments": comments_count
        })

    return results
