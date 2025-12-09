from sqlalchemy.orm import Session
from app.models.answer import Answer

def get_answers_by_question(db: Session, question_id: int):
    return db.query(Answer).filter(Answer.question_id == question_id).all()
