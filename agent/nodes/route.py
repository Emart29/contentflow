"""Route node for the contentflow agent."""

from agent.state import ContentFlowState


def route(state: ContentFlowState) -> dict:
    """Decide the final route for a pipeline run after validation."""
    if state.get("routing_decision") == "escalated":
        routing_decision = "escalated"
    else:
        validation_result = state.get("validation_result") or {}
        hard_failures = validation_result.get("hard_failures", [])
        soft_failures = validation_result.get("soft_failures", [])
        posts = state.get("posts", [])

        if hard_failures:
            routing_decision = "escalated"
        elif soft_failures or any(post.get("confidence") == "low" for post in posts):
            routing_decision = "review"
        else:
            routing_decision = "approved"

    return {
        "routing_decision": routing_decision,
        "stage": "route_complete",
    }
