# app/models/share.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Share(Base):
    __tablename__ = "shares"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
