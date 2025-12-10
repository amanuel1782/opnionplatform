from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    anonymous = Column(Integer, default=1)  # 1 = anonymous, 0 = named
    # Relationships
    user = relationship("User", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    likes = relationship("QuestionLike", back_populates="question", cascade="all, delete-orphan")
    reports = relationship("QuestionReport", back_populates="question", cascade="all, delete-orphan")

    @property
    def like_count(self):
        return len(self.likes)

    @property
    def report_count(self):
        return len(self.reports)
