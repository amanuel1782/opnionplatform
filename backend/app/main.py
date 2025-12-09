from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes_questions import router as questions_router
from app.api.v1.routes_answers import router as answers_router
from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_feed import router as feed_router
from app.api.v1.routes_health import router as health_router
from app.core.config import settings

app = FastAPI(title="Opinion Platform API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(questions_router, prefix="/api/v1/questions")
app.include_router(answers_router, prefix="/api/v1/answers")
app.include_router(feed_router, prefix="/api/v1/feed")
app.include_router(health_router, prefix="/api/v1")
