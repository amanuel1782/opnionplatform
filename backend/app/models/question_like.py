from sqlalchemy import Column, Integer, ForeignKey
from app.db.database import Base

class QuestionLike(Base):
    __tablename__ = "question_likes"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
