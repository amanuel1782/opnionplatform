# app/services/content/question_service.py
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.question import Question
from app.services.events.event_aggregator import EventAggregator
from app.events.event_types import EventTypes

class QuestionService:
    """
    Handles business logic for Questions:
    - CRUD operations
    - Engagement metrics
    - Top content
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_aggregator = EventAggregator(db)

    # ----------------------------
    # CRUD operations
    # ----------------------------
    def create_question(self, title: str, content: str, user_id: Optional[int] = None, anonymous: bool = False) -> Question:
        from app.services.events.event_logger import log_event
        q = Question(
            title=title,
            content=content,
            user_id=None if anonymous else user_id
        )
        self.db.add(q)
        self.db.commit()
        self.db.refresh(q)

        log_event(
            self.db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.QUESTION_CREATED,
            target_type="question",
            target_id=q.id,
            owner_id=q.user_id,
            is_anonymous=anonymous,
            metadata={"title": title}
        )
        self.db.commit()
        return q

    def update_question(self, question: Question, title: Optional[str] = None, content: Optional[str] = None, anonymous: Optional[bool] = None) -> Question:
        from app.services.events.event_logger import log_event
        changes = {}
        if title and title != question.title:
            changes["title"] = {"old": question.title, "new": title}
            question.title = title
        if content and content != question.content:
            changes["content"] = {"old": question.content, "new": content}
            question.content = content
        if anonymous is not None:
            old = question.user_id is None
            question.user_id = None if anonymous else question.user_id
            changes["anonymous"] = {"old": old, "new": anonymous}

        self.db.commit()
        self.db.refresh(question)

        if changes:
            log_event(
                self.db,
                actor_id=question.user_id,
                actor_role="user",
                event_type=EventTypes.QUESTION_EDITED,
                target_type="question",
                target_id=question.id,
                owner_id=question.user_id,
                is_anonymous=question.user_id is None,
                metadata=changes
            )
            self.db.commit()
        return question

    def delete_question(self, question: Question) -> None:
        from app.services.events.event_logger import log_event
        question.deleted_at = datetime.utcnow()
        self.db.commit()

        log_event(
            self.db,
            actor_id=question.user_id,
            actor_role="user",
            event_type=EventTypes.QUESTION_DELETED,
            target_type="question",
            target_id=question.id,
            owner_id=question.user_id,
            is_anonymous=question.user_id is None,
            metadata={"title": question.title}
        )
        self.db.commit()

    # ----------------------------
    # Engagement & scoring
    # ----------------------------
    def get_engagement_metrics(self, question_id: int, last_days: Optional[int] = None, weight_decay: Optional[float] = None) -> Dict:
        start_date = None
        if last_days:
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=last_days)
        return self.event_aggregator.get_engagement_metrics("question", question_id, start_date=start_date, weight_decay=weight_decay)
