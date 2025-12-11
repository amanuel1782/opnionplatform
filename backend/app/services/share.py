# app/services/share.py
import base64, hashlib, time
from app.core.config import settings
from urllib.parse import quote_plus

def generate_share_token(entity_type: str, entity_id: int) -> str:
    raw = f"{entity_type}:{entity_id}:{int(time.time())}"
    token = base64.urlsafe_b64encode(hashlib.sha1(raw.encode()).digest())[:12].decode()
    return token

def build_share_url(entity_type: str, entity_id: int, token: str) -> str:
    return f"{settings.FRONTEND_BASE_URL}/{entity_type}/{entity_id}?share={quote_plus(token)}"
