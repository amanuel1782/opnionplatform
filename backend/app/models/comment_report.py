# models/comment_report.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class CommentReport(Base):
    __tablename__ = "comment_reports"

    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey("comments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
