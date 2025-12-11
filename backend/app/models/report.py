# app/models/report.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    content_type = Column(String, nullable=False)  # 'question'/'answer'/'comment'
    content_id = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
