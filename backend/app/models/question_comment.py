# models/question_comment.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class QuestionComment(Base):
    __tablename__ = "question_comments"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
