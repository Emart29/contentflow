"""Extract node for the contentflow agent."""

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm, get_model_info
from agent.state import ContentFlowState
from models.output import EscalationFlag


REQUIRED_EXTRACTION_FIELDS = {
    "key_ideas",
    "primary_audience",
    "content_tone",
    "suggested_cta",
    "sensitive_topics",
    "confidence",
}


def _extract_prompt_path() -> Path:
    """Return the path to the extractor system prompt."""
    return Path(__file__).resolve().parents[2] / "prompts" / "extract.md"


async def extract(state: ContentFlowState) -> dict:
    """Extract structured marketing insights from ingested blog text."""
    if state.get("routing_decision") == "escalated":
        return {}

    system_prompt = _extract_prompt_path().read_text(encoding="utf-8")
    raw_text = state.get("raw_text") or ""

    if len(raw_text) > 6000:
        raw_text = f"{raw_text[:6000]}\n\n[Note: text truncated to 6000 chars for processing]"

    user_message = f"Blog post text:\n\n{raw_text}"
    llm = get_llm()
    response = await llm.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
    )

    try:
        extraction = json.loads(response.content)
    except json.JSONDecodeError:
        return {
            "flags": [
                EscalationFlag(
                    reason="EXTRACTION_PARSE_ERROR",
                    stage="extract",
                    detail=response.content[:200],
                ).model_dump()
            ],
            "routing_decision": "escalated",
            "stage": "extract_failed",
        }

    flags = []
    missing_fields = sorted(REQUIRED_EXTRACTION_FIELDS - set(extraction))

    if missing_fields:
        flags.append(
            EscalationFlag(
                reason="EXTRACTION_INCOMPLETE",
                stage="extract",
                detail=f"Missing: {missing_fields}",
            ).model_dump()
        )

    if extraction.get("confidence") == "low":
        flags.append(
            EscalationFlag(
                reason="LOW_CONFIDENCE_EXTRACTION",
                stage="extract",
                detail=extraction.get("notes", "No detail provided"),
            ).model_dump()
        )

    sensitive_topics = extraction.get("sensitive_topics") or []
    if sensitive_topics:
        flags.append(
            EscalationFlag(
                reason="SENSITIVE_TOPICS_DETECTED",
                stage="extract",
                detail=", ".join(sensitive_topics),
            ).model_dump()
        )

    return {
        "extraction": extraction,
        "flags": flags,
        "llm_info": get_model_info(),
        "stage": "extract_complete",
    }
