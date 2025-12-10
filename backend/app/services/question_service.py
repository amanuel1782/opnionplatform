from sqlalchemy.orm import Session
from app.crud.crud_question import get_question
from app.crud.crud_answer import get_answers_by_question

def get_question_with_stats(db: Session, question_id: int):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return None

    share_url = f"https://yourfrontend.com/questions/{question.id}"

    return QuestionOut(
        id=question.id,
        title=question.title,
        content=question.content,
        created_at=question.created_at,
        user=question.user,
        answers=question.answers,
        like_count=question.like_count,
        answer_count=len(question.answers),
        share_url=share_url,
    )

    question = get_question(db, question_id)
    if not question:
        return None

    answers = get_answers_by_question(db, question_id)
    answer_count = len(answers)

    # placeholder likes count (if you have likes table, query it here)
    likes = 0  

    return {
        "question": question,
        "answers": answers,
        "answer_count": answer_count,
        "likes": likes
    }

def report_question(db: Session, question_id: int, reason: str):
    print(f"Reported question {question_id} for {reason}")
    return {"status": "reported"}

def share_question(question_id: int):
    share_url = f"https://yourfrontend.com/questions/{question_id}"
    return {"share_url": share_url}
