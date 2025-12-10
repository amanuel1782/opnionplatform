import httpx

async def dispatch_answer_to_services(answer_data: dict):
    """
    Send answer to all internal ML/statistics services.
    """

    services = [
        "http://stats-service/analyze",
        "http://ai-summary/summarize",
        "http://analytics/track"
    ]

    async with httpx.AsyncClient(timeout=5) as client:
        for url in services:
            try:
                await client.post(url, json=answer_data)
            except Exception:
                pass  # log failure later
