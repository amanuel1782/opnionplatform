class EventTypes:
    # -------------------------
    # CONTENT ACTIONS
    # -------------------------
    QUESTION_CREATED = "question_created"
    QUESTION_EDITED = "question_edited"
    QUESTION_DELETED = "question_deleted"

    ANSWER_CREATED = "answer_created"
    ANSWER_EDITED = "answer_edited"
    ANSWER_DELETED = "answer_deleted"

    COMMENT_CREATED = "comment_created"
    COMMENT_EDITED = "comment_edited"
    COMMENT_DELETED = "comment_deleted"

    # -------------------------
    # ENGAGEMENT
    # -------------------------
    QUESTION_VIEWED = "question_viewed"
    ANSWER_VIEWED = "answer_viewed"
    COMMENT_VIEWED = "comment_viewed"

    QUESTION_LIKED = "question_liked"
    ANSWER_LIKED = "answer_liked"
    COMMENT_LIKED = "comment_liked"

    QUESTION_DISLIKED = "question_disliked"
    ANSWER_DISLIKED = "answer_disliked"
    COMMENT_DISLIKED = "comment_disliked"

    QUESTION_REPORTED = "question_reported"
    ANSWER_REPORTED = "answer_reported"
    COMMENT_REPORTED = "comment_reported"

    # -------------------------
    # SHARES
    # -------------------------
    QUESTION_SHARED = "question_shared"
    ANSWER_SHARED = "answer_shared"
    COMMENT_SHARED = "comment_shared"

    # -------------------------
    # SEARCH EVENTS
    # -------------------------
    SEARCH_PERFORMED = "search_performed"
    SEARCH_CLICK = "search_click"

    # -------------------------
    # NAVIGATION
    # -------------------------
    FEED_ITEM_SHOWN = "feed_item_shown"
    FEED_ITEM_OPENED = "feed_item_opened"

    # -------------------------
    # SOCIAL
    # -------------------------
    USER_FOLLOWED = "user_followed"
    USER_UNFOLLOWED = "user_unfollowed"
    TOPIC_FOLLOWED = "topic_followed"
    TOPIC_UNFOLLOWED = "topic_unfollowed"

    # -------------------------
    # SYSTEM
    # -------------------------
    LOGIN = "login"
    LOGOUT = "logout"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
