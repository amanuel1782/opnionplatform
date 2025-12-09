from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate
from app.models.user import User
from app.db.database import get_db
from app.core.security import create_access_token

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/signup")
def signup(data: UserCreate, db: Session = Depends(get_db)):
    user = User(username=data.username, hashed_password=pwd.hash(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created", "user_id": user.id}

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not pwd.verify(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=token)
