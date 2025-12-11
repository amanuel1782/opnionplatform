from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)

    user_id = Column(Integer, ForeignKey("users.id"))
    anonymous = Column(Boolean, default=False)

    views = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    status = Column(String, default="active")  # active, closed, flagged
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete")
    likes = relationship("QuestionLike", cascade="all, delete")
    reports = relationship("QuestionReport", cascade="all, delete")
    comments = relationship("Comment", back_populates="question", cascade="all, delete")

    @property
    def like_count(self):
        return len(self.likes)

    @property
    def report_count(self):
        return len(self.reports)
