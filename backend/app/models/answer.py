from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)

    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    anonymous = Column(Boolean, default=False)

    is_accepted = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    share_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    question = relationship("Question", back_populates="answers")
    user = relationship("User", back_populates="answers")
    likes = relationship("AnswerLike", cascade="all, delete")
    reports = relationship("AnswerReport", cascade="all, delete")
    comments = relationship("Comment", back_populates="answer", cascade="all, delete")
    @property
    def like_count(self):
        return len(self.likes)
