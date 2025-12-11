from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class QuestionShare(Base):
    __tablename__ = "question_shares"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String)  # whatsapp, telegram, copy-link...

    created_at = Column(DateTime, server_default=func.now())
