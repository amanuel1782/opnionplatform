# app/services/content/answer_service.py
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.answer import Answer
from app.services.events.event_aggregator import EventAggregator
from app.events.event_types import EventTypes

class AnswerService:
    """
    Handles business logic for Answers:
    - CRUD operations
    - Engagement metrics
    - Weighted scoring
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_aggregator = EventAggregator(db)

    # ----------------------------
    # CRUD operations
    # ----------------------------
    def create_answer(self, question_id: int, content: str, user_id: Optional[int] = None, anonymous: bool = False) -> Answer:
        from app.services.events.event_logger import log_event

        ans = Answer(
            question_id=question_id,
            content=content,
            user_id=None if anonymous else user_id
        )
        self.db.add(ans)
        self.db.commit()
        self.db.refresh(ans)

        log_event(
            self.db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.ANSWER_CREATED,
            target_type="answer",
            target_id=ans.id,
            owner_id=ans.user_id,
            is_anonymous=anonymous,
            metadata={"question_id": question_id}
        )
        self.db.commit()
        return ans

    def update_answer(self, answer: Answer, content: Optional[str] = None, anonymous: Optional[bool] = None) -> Answer:
        from app.services.events.event_logger import log_event
        changes = {}
        if content and content != answer.content:
            changes["content"] = {"old": answer.content, "new": content}
            answer.content = content
        if anonymous is not None:
            old = answer.user_id is None
            answer.user_id = None if anonymous else answer.user_id
            changes["anonymous"] = {"old": old, "new": anonymous}

        self.db.commit()
        self.db.refresh(answer)

        if changes:
            log_event(
                self.db,
                actor_id=answer.user_id,
                actor_role="user",
                event_type=EventTypes.ANSWER_EDITED,
                target_type="answer",
                target_id=answer.id,
                owner_id=answer.user_id,
                is_anonymous=answer.user_id is None,
                metadata=changes
            )
            self.db.commit()
        return answer

    def delete_answer(self, answer: Answer) -> None:
        from app.services.events.event_logger import log_event
        answer.deleted_at = datetime.utcnow()
        self.db.commit()

        log_event(
            self.db,
            actor_id=answer.user_id,
            actor_role="user",
            event_type=EventTypes.ANSWER_DELETED,
            target_type="answer",
            target_id=answer.id,
            owner_id=answer.user_id,
            is_anonymous=answer.user_id is None,
            metadata={"question_id": answer.question_id}
        )
        self.db.commit()

    # ----------------------------
    # Engagement & scoring
    # ----------------------------
    def get_engagement_metrics(self, answer_id: int, last_days: Optional[int] = None, weight_decay: Optional[float] = None) -> Dict:
        start_date = None
        if last_days:
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=last_days)
        return self.event_aggregator.get_engagement_metrics("answer", answer_id, start_date=start_date, weight_decay=weight_decay)
