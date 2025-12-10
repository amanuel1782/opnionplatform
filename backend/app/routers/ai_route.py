@router.get("/{question_id}/ai-summary")
def ai_answer_feed(
    question_id: int,
    db: Session = Depends(get_db)
):
    summary = summarize_question_answers(db, question_id)
    return {"summary": summary}
