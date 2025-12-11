# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.database import init_db
from app.routers import question_router,answer_router,comment_router

LOG = logging.getLogger("uvicorn.error")
app = FastAPI(title="Q&A Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    LOG.info("DB initialized")

# include routers
app.include_router(question_router)
app.include_router(answer_router)
app.include_router(comment_router)
