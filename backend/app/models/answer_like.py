from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class AnswerLike(Base):
    __tablename__ = "answer_likes"

    id = Column(Integer, primary_key=True)
    answer_id = Column(Integer, ForeignKey("answers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
