from fastapi import Depends, HTTPException
from app import models
from app.db import get_db
from sqlalchemy.orm import Session

# NOTE: Replace with your real auth dependency. This is a simple stub that
# looks up a user id 1 and returns it as the current user. In production,
# implement JWT/OAuth2 and return a user model.

def get_current_user(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
