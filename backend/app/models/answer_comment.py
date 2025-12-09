from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class AnswerComment(Base):
    __tablename__ = "answer_comments"

    id = Column(Integer, primary_key=True)
    answer_id = Column(Integer, ForeignKey("answers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    created_at = Column(DateTime, server_default=func.now())
