from app.models.answer_like import AnswerLike
from app.models.answer_comment import AnswerComment

@router.get("/question/{question_id}")
def get_answers(question_id: int, db: Session = Depends(get_db)):
    answers = (
        db.query(Answer)
        .filter(Answer.question_id == question_id)
        .all()
    )

    results = []
    for a in answers:
        likes_count = db.query(AnswerLike).filter(AnswerLike.answer_id == a.id).count()
        comments_count = db.query(AnswerComment).filter(AnswerComment.answer_id == a.id).count()

        results.append({
            "id": a.id,
            "content": a.content,
            "anonymous": a.anonymous,
            "user_id": None if a.anonymous else a.user_id,
            "created_at": a.created_at,
            "likes": likes_count,
            "comments": comments_count
        })

    return results
