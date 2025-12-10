from sqlalchemy.orm import Session
from app.models.answer import Answer
import openai   # or your AI provider

def summarize_question_answers(db: Session, question_id: int):
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    combined = "\n".join([f"- {a.content}" for a in answers])

    if not combined:
        return "No answers yet."

    prompt = (
        "Summarize the following answers:\n"
        f"{combined}\n\n"
        "Provide a concise summary:"
    )

    # Replace with your provider
    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]
