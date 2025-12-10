from sqlalchemy.orm import Session
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.answer_comment import AnswerComment

def create_answer(db: Session, question_id: int, user_id: int, content: str, anonymous: int):
    answer = Answer(
        question_id=question_id,
        user_id=user_id,
        content=content,
        anonymous=anonymous,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def toggle_answer_like(db: Session, answer_id: int, user_id: int):
    existing = db.query(AnswerLike).filter(
        AnswerLike.answer_id == answer_id,
        AnswerLike.user_id == user_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return False  # unliked

    like = AnswerLike(answer_id=answer_id, user_id=user_id)
    db.add(like)
    db.commit()
    return True  # liked


def add_comment(db: Session, answer_id: int, user_id: int, content: str):
    c = AnswerComment(
        answer_id=answer_id,
        user_id=user_id,
        content=content
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
