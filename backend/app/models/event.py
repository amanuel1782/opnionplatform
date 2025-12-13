from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Float
)
from sqlalchemy.sql import func
from app.db.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # =========================
    # ACTOR (who did the action)
    # =========================
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String, nullable=True)  # user | professional | admin
    is_anonymous = Column(Boolean, default=False)

    # =========================
    # TARGET (what was acted on)
    # =========================
    event_type = Column(String, index=True, nullable=False)
    target_type = Column(String, index=True, nullable=False)  # question | answer | comment
    target_id = Column(Integer, index=True, nullable=False)

    # =========================
    # OWNER (who owns the content)
    # =========================
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    owner_type = Column(String, default="user")  # future-proofing

    # =========================
    # CONTEXT (critical for feeds & analytics)
    # =========================
    session_id = Column(String, nullable=True, index=True)
    request_id = Column(String, nullable=True, index=True)
    feed_id = Column(String, nullable=True)
    position = Column(Integer, nullable=True)
    source = Column(String, nullable=True)        # web | ios | android
    referrer = Column(String, nullable=True)
    app_version = Column(String, nullable=True)

    # =========================
    # TELEMETRY (keep – very valuable)
    # =========================
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    user_geo = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)

    # =========================
    # RANKING / FEED CACHE (NOT source of truth)
    # =========================
    weight = Column(Float, default=0.0)
    score = Column(Float, default=0.0)
    rank_reason = Column(String, nullable=True)

    # =========================
    # MISC
    # =========================
    metadata = Column(JSON, default=dict)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
