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

    # generic FK holder for Q / A / parent Comment
    target_type = Column(String)    # "question" | "answer" | "comment"
    target_id = Column(Integer)     # dynamic foreign reference

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    is_deleted = Column(Boolean, default=False)

    # Counters
    likes_count = Column(Integer, default=0)
    dislikes_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="comments")

    # dynamic target relationships
    question = relationship("Question", back_populates="comments", foreign_keys=[], primaryjoin="and_(Comment.target_id==Question.id, Comment.target_type=='question')")
    answer = relationship("Answer", back_populates="comments", foreign_keys=[], primaryjoin="and_(Comment.target_id==Answer.id, Comment.target_type=='answer')")

    # reactions
    likes = relationship("CommentLike", cascade="all, delete-orphan")
    dislikes = relationship("CommentDislike", cascade="all, delete-orphan")

    # recursive replies (comment on comment)
    replies = relationship(
        "Comment",
        cascade="all, delete-orphan",
        primaryjoin="and_(Comment.target_id==Comment.id, Comment.target_type=='comment')"
    )
