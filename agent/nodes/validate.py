"""Validate node for the contentflow agent."""

from agent.state import ContentFlowState
from models.output import EscalationFlag


UNVERIFIED_STAT_PATTERNS = [
    "studies show",
    "research proves",
    "according to experts",
    "clinically proven",
    "scientifically proven",
    "doctors recommend",
]

FIRST_PERSON_PATTERNS = [
    " I built",
    " I created",
    " I think",
    " I recently",
]


def _append_flag(flags: list[dict], reason: str, detail: str) -> None:
    """Append a validation flag."""
    flags.append(
        EscalationFlag(
            reason=reason,
            stage="validate",
            detail=detail,
        ).dict()
    )


def validate(state: ContentFlowState) -> dict:
    """Run deterministic validation checks against generated posts."""
    config = state["config"]
    posts = state.get("posts", [])
    extraction = state.get("extraction") or {}
    blocked_terms = config.get("blocked_terms", [])

    flags = []
    hard_failures = []
    soft_failures = []

    for post in posts:
        platform = post.get("platform", "unknown")
        content = post.get("content", "")
        content_lower = content.lower()

        for term in blocked_terms:
            if term.lower() in content_lower:
                reason = "BLOCKED_TERM_DETECTED"
                hard_failures.append(reason)
                _append_flag(flags, reason, f"{platform}: blocked term '{term}' found")

        for pattern in UNVERIFIED_STAT_PATTERNS:
            if pattern in content_lower:
                reason = "UNVERIFIED_CLAIMS_DETECTED"
                hard_failures.append(reason)
                _append_flag(flags, reason, f"{platform}: '{pattern}' found")

        if content.startswith("I ") or any(pattern in content for pattern in FIRST_PERSON_PATTERNS):
            reason = "FIRST_PERSON_DETECTED"
            hard_failures.append(reason)
            _append_flag(flags, reason, f"{platform}: first-person phrasing found")

        if post.get("confidence") == "low":
            reason = "LOW_CONFIDENCE_POST"
            soft_failures.append(reason)
            _append_flag(flags, reason, f"{platform}: post confidence is low")

        if platform == "twitter" and post.get("char_count", len(content)) > 260:
            reason = "TWITTER_NEAR_LIMIT"
            soft_failures.append(reason)
            _append_flag(flags, reason, "twitter: post is over 260 characters")

    sensitive_topics = extraction.get("sensitive_topics") or []
    if sensitive_topics:
        reason = "SENSITIVE_TOPICS_PRESENT"
        soft_failures.append(reason)
        _append_flag(flags, reason, ", ".join(sensitive_topics))

    if config.get("require_human_review") is True:
        reason = "MANUAL_REVIEW_REQUESTED"
        soft_failures.append(reason)
        _append_flag(flags, reason, "Human review is required by run config")

    validation_result = {
        "total_posts_checked": len(posts),
        "hard_failures": hard_failures,
        "soft_failures": soft_failures,
        "passed": not hard_failures,
    }

    return {
        "validation_result": validation_result,
        "flags": flags,
        "stage": "validate_complete",
    }
