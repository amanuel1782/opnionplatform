# app/services/users/user_profile_metrics.py
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.services.users.user_activity_service import UserActivityService
from app.services.events.event_aggregator import EventAggregator
from datetime import datetime, timedelta

class UserProfileMetrics:
    """
    Computes user profile metrics combining activity, engagement, and content contributions.
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = UserActivityService(db)
        self.event_aggregator = EventAggregator(db)

    # ----------------------------
    # General metrics for user profile
    # ----------------------------
    def get_profile_metrics(self, user_id: int, last_days: int = 30) -> Dict:
        """
        Returns metrics for a user profile, including activity, engagement, and contribution scores.
        """
        activity_summary = self.activity_service.get_user_activity_summary(user_id, last_days=last_days)
        last_active = self.activity_service.get_last_active(user_id)

        # Contributions: questions + answers + comments
        total_contributions = (
            activity_summary.get("questions_created", 0) +
            activity_summary.get("answers_created", 0) +
            activity_summary.get("comments_created", 0)
        )

        # Engagement received on user's content
        engagement_scores = self.event_aggregator.aggregate_scores(
            target_type="question",
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=last_days)
        )
        engagement_scores.update(
            self.event_aggregator.aggregate_scores(
                target_type="answer",
                user_id=user_id,
                start_date=datetime.utcnow() - timedelta(days=last_days)
            )
        )
        engagement_scores.update(
            self.event_aggregator.aggregate_scores(
                target_type="comment",
                user_id=user_id,
                start_date=datetime.utcnow() - timedelta(days=last_days)
            )
        )

        profile_metrics = {
            "user_id": user_id,
            "total_contributions": total_contributions,
            "activity_summary": activity_summary,
            "last_active": last_active,
            "engagement_scores": engagement_scores,
            "overall_score": sum(engagement_scores.values()) if engagement_scores else 0.0
        }

        return profile_metrics
