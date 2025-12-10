from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.question import Question
from app.models.question_like import QuestionLike
from app.models.answer import Answer
from app.services.ai_summary import summarize_question_answers

router = APIRouter()

@router.get("/{question_id}/summary")
def get_ai_summary(question_id: int, db: Session = Depends(get_db)):
    summary = summarize_question_answers(db, question_id)
    return {"summary": summary}
@router.get("/{question_id}/details")
def get_question_details(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    answer_count = db.query(Answer).filter(Answer.question_id == question_id).count()
    like_count = db.query(QuestionLike).filter(QuestionLike.question_id == question_id).count()

    return {
        "id": q.id,
        "title": q.title,
        "content": q.content,
        "created_at": q.created_at,
        "asked_by": q.user.username if q.user else None,
        "answer_count": answer_count,
        "likes": like_count,
        "share_url": f"https://yourfrontend.com/questions/{q.id}",
    }