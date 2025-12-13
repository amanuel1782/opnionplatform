# app/services/content/comment_service.py
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.services.events.event_aggregator import EventAggregator
from app.events.event_types import EventTypes

class CommentService:
    """
    Handles business logic for Comments:
    - CRUD operations
    - Engagement metrics
    - Nested comments
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_aggregator = EventAggregator(db)

    # ----------------------------
    # CRUD operations
    # ----------------------------
    def create_comment(self, target_type: str, target_id: int, content: str, user_id: Optional[int] = None, anonymous: bool = False) -> Comment:
        from app.services.events.event_logger import log_event

        c = Comment(
            body=content,
            target_type=target_type,
            target_id=target_id,
            user_id=None if anonymous else user_id
        )
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)

        log_event(
            self.db,
            actor_id=user_id,
            actor_role="user",
            event_type=EventTypes.COMMENT_CREATED,
            target_type="comment",
            target_id=c.id,
            owner_id=c.user_id,
            is_anonymous=anonymous,
            metadata={"target_type": target_type, "target_id": target_id}
        )
        self.db.commit()
        return c

    def update_comment(self, comment: Comment, content: Optional[str] = None, anonymous: Optional[bool] = None) -> Comment:
        from app.services.events.event_logger import log_event
        changes = {}
        if content and content != comment.body:
            changes["content"] = {"old": comment.body, "new": content}
            comment.body = content
        if anonymous is not None:
            old = comment.user_id is None
            comment.user_id = None if anonymous else comment.user_id
            changes["anonymous"] = {"old": old, "new": anonymous}

        self.db.commit()
        self.db.refresh(comment)

        if changes:
            log_event(
                self.db,
                actor_id=comment.user_id,
                actor_role="user",
                event_type=EventTypes.COMMENT_EDITED,
                target_type="comment",
                target_id=comment.id,
                owner_id=comment.user_id,
                is_anonymous=comment.user_id is None,
                metadata=changes
            )
            self.db.commit()
        return comment

    def delete_comment(self, comment: Comment) -> None:
        from app.services.events.event_logger import log_event
        comment.deleted_at = datetime.utcnow()
        self.db.commit()

        log_event(
            self.db,
            actor_id=comment.user_id,
            actor_role="user",
            event_type=EventTypes.COMMENT_DELETED,
            target_type="comment",
            target_id=comment.id,
            owner_id=comment.user_id,
            is_anonymous=comment.user_id is None,
            metadata={"target_type": comment.target_type, "target_id": comment.target_id}
        )
        self.db.commit()

    # ----------------------------
    # Engagement & nested comments
    # ----------------------------
    def get_engagement_metrics(self, comment_id: int, last_days: Optional[int] = None, weight_decay: Optional[float] = None) -> Dict:
        start_date = None
        if last_days:
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=last_days)
        return self.event_aggregator.get_engagement_metrics("comment", comment_id, start_date=start_date, weight_decay=weight_decay)
