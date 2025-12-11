from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class AnswerShare(Base):
    __tablename__ = "answer_shares"

    id = Column(Integer, primary_key=True)
    answer_id = Column(Integer, ForeignKey("answers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String)

    created_at = Column(DateTime, server_default=func.now())
