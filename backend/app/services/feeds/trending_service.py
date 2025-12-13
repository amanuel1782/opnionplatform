# app/services/feeds/trending_service.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.services.events.event_aggregator import EventAggregator

class TrendingService:
    """
    Computes trending content based on engagement and recency.
    Uses weighted and decayed scores for ranking.
    """

    def __init__(self, db):
        self.db = db
        self.event_aggregator = EventAggregator(db)

    def get_trending(
        self,
        target_type: str,
        top_n: int = 10,
        last_days: int = 7,
        decay_hours: int = 72,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Returns top N trending items of a given type.
        """
        from app.models import question, answer, comment

        start_date = datetime.utcnow() - timedelta(days=last_days)

        # Fetch all relevant targets
        model_map = {"question": question.Question, "answer": answer.Answer, "comment": comment.Comment}
        Model = model_map.get(target_type)
        if not Model:
            return []

        query = self.db.query(Model).filter(Model.deleted_at.is_(None), Model.created_at >= start_date)
        if filters:
            for attr, val in filters.items():
                query = query.filter(getattr(Model, attr) == val)

        targets = query.all()
        target_ids = [t.id for t in targets]

        # Compute scores using EventAggregator
        scores = self.event_aggregator.aggregate_scores(
            target_type=target_type,
            target_ids=target_ids,
            start_date=start_date,
            decay_hours=decay_hours
        )

        # Sort and return top N
        top_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"target_id": tid, "score": score} for tid, score in top_items]
