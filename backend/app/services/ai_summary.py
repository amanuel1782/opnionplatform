# app/services/ai_summary_service.py
import os
from typing import List
import logging

LOG = logging.getLogger("ai_summary")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

def summarize_question_answers(title: str, content: str, answers: List[str]) -> str:
    """
    Simple summary aggregator. If OPENAI_API_KEY is set, you can expand this
    to call the OpenAI/other LLM. For now we provide a safe fallback summary.
    """
    if not answers:
        return "No answers yet."

    # Basic heuristic summary: show top 3 answers (by length) plus short merge
    best = sorted(answers, key=len, reverse=True)[:3]
    summary = f"Question: {title}\n\n"
    summary += "Summary of top answers:\n"
    for i, a in enumerate(best, 1):
        # trim to 300 chars
        text = a if len(a) <= 300 else a[:297] + "..."
        summary += f"{i}. {text}\n\n"

    # Optionally, you could call an LLM here if configured
    if OPENAI_API_KEY:
        LOG.info("OPENAI_API_KEY set: call external LLM here (not implemented).")

    return summary
