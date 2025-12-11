from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    content = Column(String)

    user_id = Column(Integer, ForeignKey("users.id"))
    anonymous = Column(Boolean, default=False)

    target_type = Column(String)  # "question", "answer", "comment"
    target_id = Column(Integer)   # points to question_id, answer_id, or parent comment_id

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    is_deleted = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="comments")
    question = relationship("Question", back_populates="comments")
    answer = relationship("Answer", back_populates="comments")
    replies = relationship("Comment")
