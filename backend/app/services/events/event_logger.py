# app/services/events/event_logger.py
from typing import Optional
from sqlalchemy.orm import Session
from app.models.event import Event

class EventLogger:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        actor_id: Optional[int],
        actor_role: Optional[str],
        event_type: str,
        target_type: str,
        target_id: int,
        owner_id: Optional[int] = None,
        owner_type: str = "user",
        is_anonymous: bool = False,
        metadata: Optional[dict] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        feed_id: Optional[str] = None,
        position: Optional[int] = None,
        source: Optional[str] = None,
        referrer: Optional[str] = None,
        app_version: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_geo: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ) -> Event:
        """
        Create and persist an Event in the database.
        """
        evt = Event(
            actor_id=actor_id,
            actor_role=actor_role,
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            owner_id=owner_id,
            owner_type=owner_type,
            is_anonymous=is_anonymous,
            metadata=metadata or {},
            session_id=session_id,
            request_id=request_id,
            feed_id=feed_id,
            position=position,
            source=source,
            referrer=referrer,
            app_version=app_version,
            ip_address=ip_address,
            user_agent=user_agent,
            user_geo=user_geo,
            latency_ms=latency_ms
        )
        self.db.add(evt)
        self.db.commit()
        self.db.refresh(evt)
        return evt
