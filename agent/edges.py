"""Edge definitions for the contentflow agent."""

from agent.state import ContentFlowState


def decide_route(state: ContentFlowState) -> str:
    """Return the routing decision for LangGraph conditional edges."""
    return state.get("routing_decision") or "escalated"
