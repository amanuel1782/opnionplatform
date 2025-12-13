# app/services/events/event_reader.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.event import Event

class EventReader:
    """
    EventReader provides flexible, efficient access to Event data.
    Supports filters, aggregations, pagination, and grouping.
    """

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------
    # Fetch events with filters
    # ----------------------------
    def get_events(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        actor_id: Optional[int] = None,
        session_id: Optional[str] = None,
        feed_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = 100,
        offset: int = 0,
        order_desc: bool = True
    ) -> List[Event]:
        """
        Returns a list of Event objects filtered by various criteria.
        """
        query = self.db.query(Event)

        if target_type:
            query = query.filter(Event.target_type == target_type)
        if target_id:
            query = query.filter(Event.target_id == target_id)
        if actor_id:
            query = query.filter(Event.actor_id == actor_id)
        if session_id:
            query = query.filter(Event.session_id == session_id)
        if feed_id:
            query = query.filter(Event.feed_id == feed_id)
        if start_date:
            query = query.filter(Event.created_at >= start_date)
        if end_date:
            query = query.filter(Event.created_at <= end_date)

        if order_desc:
            query = query.order_by(Event.created_at.desc())
        else:
            query = query.order_by(Event.created_at.asc())

        if limit is not None:
            query = query.offset(offset).limit(limit)

        return query.all()

    # ----------------------------
    # Aggregate events with group_by
    # ----------------------------
    def aggregate_events(
        self,
        group_by: str = "event_type",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns aggregated event counts grouped by a column (event_type, user_id, session_id, etc.).
        Example:
        [{"event_type": "question_liked", "count": 10}, ...]
        """
        query = self.db.query(getattr(Event, group_by), func.count().label("count"))

        if filters:
            for k, v in filters.items():
                # Handle special filter suffixes for date ranges
                if k.endswith("__gte"):
                    col = getattr(Event, k.replace("__gte", ""))
                    query = query.filter(col >= v)
                elif k.endswith("__lte"):
                    col = getattr(Event, k.replace("__lte", ""))
                    query = query.filter(col <= v)
                else:
                    query = query.filter(getattr(Event, k) == v)

        query = query.group_by(getattr(Event, group_by))
        results = query.all()

        return [{group_by: r[0], "count": r[1]} for r in results]

    # ----------------------------
    # Count events for target(s)
    # ----------------------------
    def count_events(
        self,
        target_type: Optional[str] = None,
        target_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Returns total number of events matching filters.
        """
        query = self.db.query(func.count(Event.id))

        if target_type:
            query = query.filter(Event.target_type == target_type)
        if target_ids:
            query = query.filter(Event.target_id.in_(target_ids))
        if start_date:
            query = query.filter(Event.created_at >= start_date)
        if end_date:
            query = query.filter(Event.created_at <= end_date)

        return query.scalar() or 0
