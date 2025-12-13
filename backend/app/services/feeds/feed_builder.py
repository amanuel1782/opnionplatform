# app/services/feeds/feed_builder.py
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.services.content import question_service, answer_service, comment_service
from app.services.events.event_aggregator import EventAggregator
from app.events.event_types import EventTypes

class FeedBuilder:
    """
    Builds personalized feeds for users.
    Fetches content, computes engagement metrics, applies ranking & filtering.
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_aggregator = EventAggregator(db)
        self.question_service = question_service.QuestionService(db)
        self.answer_service = answer_service.AnswerService(db)
        self.comment_service = comment_service.CommentService(db)

    # ----------------------------
    # Core feed building
    # ----------------------------
    def build_user_feed(
        self,
        user_id: int,
        limit: int = 20,
        include_answers: bool = True,
        include_comments: bool = False,
        since_days: int = 30
    ) -> List[Dict]:
        """
        Build a personalized feed for a user:
        - Fetch recent questions
        - Include engagement metrics
        - Optional answers & comments
        """
        from app.models.question import Question

        start_date = datetime.utcnow() - timedelta(days=since_days)
        questions = self.db.query(Question)\
            .filter(Question.deleted_at.is_(None), Question.created_at >= start_date)\
            .order_by(Question.created_at.desc())\
            .limit(limit).all()

        feed_items = []
        for q in questions:
            metrics = self.event_aggregator.get_engagement_metrics("question", q.id, start_date=start_date)
            item = {
                "id": q.id,
                "type": "question",
                "title": q.title,
                "content": q.content,
                "user_id": q.user_id,
                "is_anonymous": q.user_id is None,
                "created_at": q.created_at,
                "engagement_metrics": metrics
            }

            if include_answers:
                answers = self.answer_service.get_engagement_metrics(q.id)
                item["answers_metrics"] = answers

            feed_items.append(item)

        # Apply ranking
        ranked_feed = FeedRankingEngine.rank_items(feed_items)
        return ranked_feed
