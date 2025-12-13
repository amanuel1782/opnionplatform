# app/services/users/user_activity_service.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.event import Event
from app.events.event_types import EventTypes
from app.services.events.event_aggregator import EventAggregator

class UserActivityService:
    """
    Tracks and aggregates user activity.
    Provides activity summaries, engagement counts, and last seen info.
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_aggregator = EventAggregator(db)

    # ----------------------------
    # Fetch all events for a user
    # ----------------------------
    def get_user_events(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        target_type: Optional[str] = None
    ) -> List[Event]:
        """
        Returns all events performed by a user optionally filtered by date and target_type.
        """
        return self.event_aggregator.reader.get_events(
            actor_id=user_id,
            target_type=target_type,
            start_date=start_date,
            end_date=end_date
        )

    # ----------------------------
    # Aggregate activity metrics
    # ----------------------------
    def get_user_activity_summary(
        self,
        user_id: int,
        last_days: int = 30
    ) -> Dict[str, int]:
        """
        Returns activity counts for the last N days.
        """
        start_date = datetime.utcnow() - timedelta(days=last_days)
        events = self.get_user_events(user_id=user_id, start_date=start_date)

        summary = {
            "total_events": len(events),
            "questions_created": 0,
            "answers_created": 0,
            "comments_created": 0,
            "likes": 0,
            "dislikes": 0,
            "reports": 0,
            "shares": 0
        }

        for e in events:
            if e.event_type in [EventTypes.QUESTION_CREATED, EventTypes.ANSWER_CREATED, EventTypes.COMMENT_CREATED]:
                if e.event_type == EventTypes.QUESTION_CREATED:
                    summary["questions_created"] += 1
                elif e.event_type == EventTypes.ANSWER_CREATED:
                    summary["answers_created"] += 1
                elif e.event_type == EventTypes.COMMENT_CREATED:
                    summary["comments_created"] += 1
            elif e.event_type in [EventTypes.QUESTION_LIKED, EventTypes.ANSWER_LIKED, EventTypes.COMMENT_LIKED]:
                summary["likes"] += 1
            elif e.event_type in [EventTypes.QUESTION_DISLIKED, EventTypes.ANSWER_DISLIKED, EventTypes.COMMENT_DISLIKED]:
                summary["dislikes"] += 1
            elif e.event_type in [EventTypes.QUESTION_REPORTED, EventTypes.ANSWER_REPORTED, EventTypes.COMMENT_REPORTED]:
                summary["reports"] += 1
            elif e.event_type in [EventTypes.QUESTION_SHARED, EventTypes.ANSWER_SHARED, EventTypes.COMMENT_SHARED]:
                summary["shares"] += 1

        return summary

    # ----------------------------
    # Last active time
    # ----------------------------
    def get_last_active(self, user_id: int) -> Optional[datetime]:
        """
        Returns the timestamp of the most recent user event.
        """
        events = self.get_user_events(user_id=user_id)
        if not events:
            return None
        return max(e.created_at for e in events)
