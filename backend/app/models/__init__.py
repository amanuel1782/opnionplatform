# app/models/__init__.py
# convenient import for init_db
from .user import User  # noqa
from .question import Question  # noqa
from .answer import Answer  # noqa
from .comment import Comment  # noqa
from .question_like import QuestionLike  # noqa
from .answer_like import AnswerLike  # noqa
from .report import Report  # noqa
# app/models/__init__.py
# import models to register them with Base in init_db
from .user import User  # noqa
from .question import Question  # noqa
from .answer import Answer  # noqa
from .comment import Comment  # noqa
from .question_like import QuestionLike  # noqa
from .answer_like import AnswerLike  # noqa
from .comment_like import CommentLike  # noqa
from .report import Report  # noqa
from .share import Share  # noqa
