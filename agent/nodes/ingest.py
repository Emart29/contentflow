"""Ingest node for the contentflow agent."""

import re

import httpx
from bs4 import BeautifulSoup

from agent.state import ContentFlowState
from models.output import EscalationFlag


def _clean_text(text: str) -> str:
    """Normalize whitespace in extracted article text."""
    text = text.strip()
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _fetch_failed(status_code: int | str) -> dict:
    """Build a failed fetch state update."""
    return {
        "flags": [
            EscalationFlag(
                reason="FETCH_FAILED",
                stage="ingest",
                detail=f"HTTP {status_code}",
            ).dict()
        ],
        "routing_decision": "escalated",
        "stage": "ingest_failed",
    }


async def ingest(state: ContentFlowState) -> dict:
    """Fetch, parse, and normalize blog post text for downstream nodes."""
    try:
        state["stage"] = "ingest_running"
        provided_text = state["blog_post"].get("raw_text")
        if provided_text:
            cleaned_text = _clean_text(provided_text)
            word_count = len(cleaned_text.split())

            if word_count < 200:
                return {
                    "flags": [
                        EscalationFlag(
                            reason="INSUFFICIENT_CONTENT",
                            stage="ingest",
                            detail=f"[Observed] {word_count} words found, minimum is 200",
                        ).dict()
                    ],
                    "routing_decision": "escalated",
                    "stage": "ingest_failed",
                }

            blog_post = dict(state["blog_post"])
            blog_post["word_count"] = word_count

            return {
                "raw_text": cleaned_text,
                "blog_post": blog_post,
                "stage": "ingest_complete",
            }

        url = state["blog_post"]["url"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url)
            except httpx.HTTPError as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", "unknown")
                return _fetch_failed(status_code)

        if response.status_code != 200:
            return _fetch_failed(response.status_code)

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        container = soup.find("article") or soup.find("main") or soup.find("body")
        raw_text = container.get_text("\n", strip=True) if container else soup.get_text("\n", strip=True)
        cleaned_text = _clean_text(raw_text)
        word_count = len(cleaned_text.split())

        if word_count < 200:
            return {
                "flags": [
                    EscalationFlag(
                        reason="INSUFFICIENT_CONTENT",
                        stage="ingest",
                        detail=f"[Observed] {word_count} words found, minimum is 200",
                    ).dict()
                ],
                "routing_decision": "escalated",
                "stage": "ingest_failed",
            }

        blog_post = dict(state["blog_post"])
        blog_post["word_count"] = word_count

        return {
            "raw_text": cleaned_text,
            "blog_post": blog_post,
            "stage": "ingest_complete",
        }
    except Exception as exc:
        return {
            "flags": [
                EscalationFlag(
                    reason="INGEST_ERROR",
                    stage="ingest",
                    detail=str(exc),
                ).dict()
            ],
            "routing_decision": "escalated",
            "stage": "ingest_failed",
        }
