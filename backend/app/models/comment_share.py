# models/comment_share.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class CommentShare(Base):
    __tablename__ = "comment_shares"

    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey("comments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String)

    created_at = Column(DateTime, server_default=func.now())
