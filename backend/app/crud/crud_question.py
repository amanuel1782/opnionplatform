from sqlalchemy.orm import Session
from app.models.question import Question

def get_question(db: Session, question_id: int):
    return db.query(Question).filter(Question.id == question_id).first()
