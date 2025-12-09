from app.models.answer import Answer
from app.core.openai_client import ai

def summarize_question_answers(db, question_id):
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    text_data = "\n".join(a.content for a in answers)

    if not text_data.strip():
        return "No answers available to summarize."

    summary = ai.summarize(text_data)
    return summary
