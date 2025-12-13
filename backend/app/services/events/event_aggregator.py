# app/services/events/event_aggregator.py
from typing import Optional, List, Dict, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.event import Event
from app.services.events.event_reader import EventReader
from app.events.event_types import EventTypes

class EventAggregator:
    """
    EventAggregator computes engagement metrics for targets (questions, answers, comments)
    using EventReader for efficient DB queries. Supports time-based metrics, weighted scores,
    and custom groupings (user, session, feed).
    """

    def __init__(self, db: Session):
        self.db = db
        self.reader = EventReader(db)

    # ----------------------------
    # Basic engagement metrics for a single target
    # ----------------------------
    def get_engagement_metrics(
        self,
        target_type: str,
        target_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        weight_decay: Optional[float] = None
    ) -> Dict[str, Union[int, float]]:
        """
        Returns total counts of likes, dislikes, reports, shares, comments for a single target.
        Can filter by time and apply exponential decay weight for scoring.
        """
        events = self.reader.get_events(
            target_type=target_type,
            target_id=target_id,
            start_date=start_date,
            end_date=end_date,
            limit=None
        )

        metrics = {
            "total_events": len(events),
            "likes_events": 0,
            "dislikes_events": 0,
            "reports_events": 0,
            "shares_events": 0,
            "comments_events": 0,
            "weighted_score": 0.0
        }

        for e in events:
            # Count event types
            if e.event_type in [EventTypes.QUESTION_LIKED, EventTypes.ANSWER_LIKED, EventTypes.COMMENT_LIKED]:
                metrics["likes_events"] += 1
            elif e.event_type in [EventTypes.QUESTION_DISLIKED, EventTypes.ANSWER_DISLIKED, EventTypes.COMMENT_DISLIKED]:
                metrics["dislikes_events"] += 1
            elif e.event_type in [EventTypes.QUESTION_REPORTED, EventTypes.ANSWER_REPORTED, EventTypes.COMMENT_REPORTED]:
                metrics["reports_events"] += 1
            elif e.event_type in [EventTypes.QUESTION_SHARED, EventTypes.ANSWER_SHARED, EventTypes.COMMENT_SHARED]:
                metrics["shares_events"] += 1
            elif e.event_type.startswith("comment_"):
                metrics["comments_events"] += 1

            # Weighted score: e.g., decay recent events less
            if weight_decay is not None:
                age_hours = (datetime.utcnow() - e.created_at).total_seconds() / 3600
                decay_score = 1.0 / ((1.0 + weight_decay) ** age_hours)
                metrics["weighted_score"] += decay_score
            else:
                metrics["weighted_score"] += 1.0

        return metrics

    # ----------------------------
    # Batch metrics for multiple targets
    # ----------------------------
    def get_batch_metrics(
        self,
        target_type: str,
        target_ids: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        weight_decay: Optional[float] = None
    ) -> Dict[int, Dict[str, Union[int, float]]]:
        """
        Returns engagement metrics for multiple targets at once.
        """
        metrics_dict = {}
        for tid in target_ids:
            metrics_dict[tid] = self.get_engagement_metrics(target_type, tid, start_date, end_date, weight_decay)
        return metrics_dict

    # ----------------------------
    # Aggregation by event type or grouping
    # ----------------------------
    def aggregate_by_event_type(
        self,
        target_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: Optional[str] = None  # e.g., "user_id", "session_id", "feed_id"
    ) -> List[Dict[str, Union[str, int]]]:
        """
        Returns a list of counts grouped by event_type or custom group.
        Example output:
        [{"event_type": "question_liked", "count": 120}, ...]
        or grouped by user_id: [{"user_id": 1, "count": 5}, ...]
        """
        filters = {}
        if target_type:
            filters["target_type"] = target_type
        if start_date:
            filters["created_at__gte"] = start_date
        if end_date:
            filters["created_at__lte"] = end_date

        return self.reader.aggregate_events(group_by=group_by or "event_type", filters=filters)

    # ----------------------------
    # Predefined time windows (industry standard)
    # ----------------------------
    def get_metrics_last_days(
        self,
        target_type: str,
        target_id: int,
        days: int = 7,
        weight_decay: Optional[float] = None
    ) -> Dict[str, Union[int, float]]:
        """
        Shortcut to get metrics for the last N days.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        return self.get_engagement_metrics(target_type, target_id, start_date=start_date, end_date=None, weight_decay=weight_decay)
    # ----------------------------
    # Default weights for event types
    # ----------------------------
    DEFAULT_WEIGHTS = {
        "question_liked": 1.0,
        "question_disliked": -1.0,
        "question_reported": -2.0,
        "question_shared": 2.0,
        "answer_created": 2.0,
        "answer_liked": 1.0,
        "answer_disliked": -1.0,
        "answer_reported": -2.0,
        "answer_shared": 2.0,
        "comment_created": 1.0,
        "comment_liked": 1.0,
        "comment_disliked": -1.0,
        "comment_reported": -2.0,
        "comment_shared": 2.0
    }

    # ----------------------------
    # Time decay function
    # ----------------------------
    @staticmethod
    def decay_score(score: float, event_time: datetime, decay_hours: int = 72) -> float:
        """
        Apply exponential time decay to a score.
        Default decay: half-life of 72 hours.
        """
        age_hours = (datetime.utcnow() - event_time).total_seconds() / 3600
        decay_factor = 0.5 ** (age_hours / decay_hours)
        return score * decay_factor

    # ----------------------------
    # Aggregate weighted scores
    # ----------------------------
    def aggregate_scores(
        self,
        target_type: str,
        target_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        feed_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        weights: Optional[Dict[str, float]] = None,
        decay_hours: int = 72
    ) -> Dict[int, float]:
        """
        Returns weighted, time-decayed scores per target_id.
        """
        weights = weights or self.DEFAULT_WEIGHTS

        # Fetch events from EventReader
        events = self.reader.get_events(
            target_type=target_type,
            target_id=None,  # fetch all or filtered below
            actor_id=user_id,
            feed_id=feed_id,
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            limit=None
        )

        if target_ids:
            events = [e for e in events if e.target_id in target_ids]

        scores: Dict[int, float] = {}

        for e in events:
            w = weights.get(e.event_type, 0.0)
            decayed_score = self.decay_score(w, e.created_at, decay_hours)
            scores[e.target_id] = scores.get(e.target_id, 0.0) + decayed_score

        return scores

    # ----------------------------
    # Top N scoring targets
    # ----------------------------
    def top_n(
        self,
        target_type: str,
        n: int = 10,
        **kwargs
    ) -> List[Dict[str, float]]:
        """
        Returns top N targets by aggregated score.
        """
        scores = self.aggregate_scores(target_type, **kwargs)
        top_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        return [{"target_id": tid, "score": score} for tid, score in top_items]
