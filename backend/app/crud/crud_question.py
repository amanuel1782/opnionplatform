from sqlalchemy.orm import Session
from app.models.question_like import QuestionLike
from app.models.question_report import QuestionReport

def toggle_question_like(db: Session, question_id: int, user_id: int):
    existing = db.query(QuestionLike).filter(
        QuestionLike.question_id == question_id,
        QuestionLike.user_id == user_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return False  # unliked

    like = QuestionLike(question_id=question_id, user_id=user_id)
    db.add(like)
    db.commit()
    return True


def report_question(db: Session, question_id: int, user_id: int, reason: str):
    report = QuestionReport(
        question_id=question_id,
        user_id=user_id,
        reason=reason
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
