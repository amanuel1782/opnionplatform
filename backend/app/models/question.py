from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    user_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    # relationship
    answers = relationship("Answer", back_populates="question")
