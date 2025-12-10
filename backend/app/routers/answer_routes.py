from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.crud.crud_answer import (
    create_answer,
    toggle_answer_like,
    add_comment
)
from app.schemas.answer import AnswerCreate,AnswerOut
from app.schemas.comment import CommentCreate
from app.models.answer import Answer
from app.models.answer_like import AnswerLike
from app.models.answer_comment import AnswerComment

router = APIRouter(prefix="/answers", tags=["Answers"])


# --------------------------
# Create Answer
# --------------------------
@router.post("/question/{question_id}")
def write_answer(
    question_id: int,
    payload: AnswerCreate,
    db: Session = Depends(get_db),
    user_id: int = 1,  # Replace with actual auth system
):
    answer = create_answer(
        db=db,
        question_id=question_id,
        user_id=user_id,
        content=payload.content,
        anonymous=payload.anonymous
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)

    # background analytics dispatch
    background_tasks.add_task(
        dispatch_answer_to_services,
        {
            "answer_id": answer.id,
            "question_id": question_id,
            "content": payload.content,
            "anonymous": payload.anonymous,
            "user_id": current_user.id,
        }
    )

    likes = db.query(AnswerLike).filter(AnswerLike.answer_id == answer.id).count()
    comments = db.query(AnswerComment).filter(AnswerComment.answer_id == answer.id).count()

    return AnswerOut(
        id=answer.id,
        content=answer.content,
        anonymous=answer.anonymous,
        user_id=None if answer.anonymous else answer.user_id,
        created_at=answer.created_at,
        likes=likes,
        comments=comments
    )

# --------------------------
# Answer Like / Unlike
# --------------------------
@router.post("/{answer_id}/like")
def like_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    liked = toggle_answer_like(db, answer_id, user_id)
    likes = db.query(AnswerLike).filter(AnswerLike.answer_id == answer_id).count()

    return {
        "liked": liked,
        "likes": likes
    }


# --------------------------
# Add Comment to Answer
# --------------------------
@router.post("/{answer_id}/comment")
def comment_on_answer(
    answer_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    comment = add_comment(db, answer_id, user_id, payload.content)
    comment_count = db.query(AnswerComment).filter(
        AnswerComment.answer_id == answer_id
    ).count()

    return {
        "comment_id": comment.id,
        "comment": comment.content,
        "comments_total": comment_count
    }
@router.put("/answer/{answer_id}")
def edit_answer(
    answer_id: int,
    payload: AnswerBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a:
        raise HTTPException(404, "Answer not found")
    if a.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    a.content = payload.content
    a.anonymous = payload.anonymous
    db.commit()
    return {"status": "updated"}
@router.delete("/answer/{answer_id}")
def delete_answer(answer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if not a:
        raise HTTPException(404, "Answer not found")
    if a.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    db.delete(a)
    db.commit()
    return {"status": "deleted"}
