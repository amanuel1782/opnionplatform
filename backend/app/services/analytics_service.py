# app/services/analytics.py
import os, logging
import httpx
from app.core.config import settings

LOG = logging.getLogger("analytics")

ENDPOINTS = [settings.ANALYTICS_URL, settings.AI_SUMMARY_URL]

async def push_event_async(event_type: str, payload: dict):
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in ENDPOINTS:
            if not url:
                continue
            try:
                await client.post(url, json={"event": event_type, "payload": payload})
            except Exception as e:
                LOG.warning("analytics push failed: %s -> %s", url, e)

def push_event(event_type: str, payload: dict):
    LOG.info("event: %s %s", event_type, payload)
    # fire-and-forget; you may integrate BackgroundTasks call to push_event_async
