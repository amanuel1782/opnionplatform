# app/services/feeds/ranking_engine.py
from typing import List, Dict
from datetime import datetime, timedelta

class FeedRankingEngine:
    """
    Sorts feed items based on engagement metrics, recency, and custom weights.
    Can be extended for ML-based personalization.
    """

    DEFAULT_WEIGHTS = {
        "likes_events": 1.0,
        "dislikes_events": -1.0,
        "shares_events": 2.0,
        "reports_events": -2.0,
        "comments_events": 1.5
    }

    @staticmethod
    def rank_items(items: List[Dict], weights: Dict[str, float] = None, decay_hours: int = 72) -> List[Dict]:
        """
        Apply weighted scoring and time decay to rank feed items.
        """
        weights = weights or FeedRankingEngine.DEFAULT_WEIGHTS

        def compute_score(item: Dict) -> float:
            score = 0.0
            metrics = item.get("engagement_metrics", {})
            for key, weight in weights.items():
                score += metrics.get(key, 0) * weight

            # Recency decay: newer items score higher
            age_hours = (datetime.utcnow() - item.get("created_at", datetime.utcnow())).total_seconds() / 3600
            decay_factor = 0.5 ** (age_hours / decay_hours)
            return score * decay_factor

        ranked = sorted(items, key=lambda x: compute_score(x), reverse=True)
        return ranked
