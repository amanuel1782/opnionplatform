from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Relationships
    questions = relationship("Question", back_populates="user")
    answers = relationship("Answer", back_populates="user")
    question_likes = relationship("QuestionLike", back_populates="user")
    answer_likes = relationship("AnswerLike", back_populates="user")
