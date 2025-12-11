# app/core/auth_stub.py
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db

def get_current_user_id(x_user_id: Optional[str] = Header(None), db: Session = Depends(get_db)) -> int:
    """
    Lightweight auth stub: checks X-User-Id header (numeric). If not provided, uses user id 1.
    Later swap this dependency with a real get_current_user that returns a User model.
    """
    try:
        if x_user_id:
            uid = int(x_user_id)
            return uid
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")

    # fallback: ensure a default user (id=1) exists or just return 1 for dev
    return 1
