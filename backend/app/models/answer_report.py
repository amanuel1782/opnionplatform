from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class AnswerReport(Base):
    __tablename__ = "answer_reports"

    id = Column(Integer, primary_key=True)
    answer_id = Column(Integer, ForeignKey("answers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String)

    created_at = Column(DateTime, server_default=func.now())
