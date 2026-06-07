"""State definitions for the contentflow agent."""

from typing import Annotated, Literal, TypedDict
import operator


class ContentFlowState(TypedDict):
    """Shared LangGraph state for a contentflow pipeline run."""

    # Unique identifier for the current pipeline run.
    run_id: str
    # Serialized run configuration, including client and platform settings.
    config: dict
    # Serialized blog post input and source metadata.
    blog_post: dict
    # Plain text extracted or supplied from the source blog post.
    raw_text: str | None
    # Structured facts and summary extracted from the blog content.
    extraction: dict | None
    # Generated social posts, merged additively across graph nodes.
    posts: Annotated[list[dict], operator.add]
    # Escalation or review flags, merged additively across graph nodes.
    flags: Annotated[list[dict], operator.add]
    # Result payload from validation checks.
    validation_result: dict | None
    # Final routing outcome for the run.
    routing_decision: Literal["approved", "review", "escalated"] | None
    # Error message captured during pipeline execution, if any.
    error: str | None
    # Name of the current or most recently completed pipeline stage.
    stage: str
    # Unix timestamp marking when the run began.
    start_time: float
    # LLM provider and model metadata used during the run.
    llm_info: dict | None
