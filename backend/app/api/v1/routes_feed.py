from fastapi import APIRouter
from app.services.feed_service import get_feed

router = APIRouter()

@router.get("/")
def feed():
    return get_feed()
