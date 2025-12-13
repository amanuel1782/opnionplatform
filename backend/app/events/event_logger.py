from .event_types import EventTypes

async def log_event(user_id: str | None, event_type: str, metadata: dict = None):
    event = {
        "user_id": user_id,
        "event_type": event_type,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat()
    }

    # If using Kafka or Redis Streams later:
    # await stream.send("events", event)

    # For now store in DB or file:
    await db.events.insert_one(event)

    return event
