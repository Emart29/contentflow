"""Graph definition for the contentflow agent."""

import sqlite3
import time
import uuid

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

from agent.edges import decide_route
from agent.llm import get_llm, get_model_info, get_provider_name
from agent.nodes.extract import extract
from agent.nodes.generate import generate
from agent.nodes.ingest import ingest
from agent.nodes.route import route
from agent.nodes.validate import validate
from agent.state import ContentFlowState
from models.input import BlogPost, RunConfig
from models.output import PipelineResult


try:
    get_llm()
    print(f"[ContentFlow] Provider: {get_provider_name()}")
except ValueError as e:
    raise RuntimeError(f"LLM config error: {e}") from e

DB_PATH = "contentflow.db"


def _build_graph() -> StateGraph:
    b = StateGraph(ContentFlowState)
    b.add_node("ingest", ingest)
    b.add_node("extract", extract)
    b.add_node("generate", generate)
    b.add_node("validate", validate)
    b.add_node("route", route)
    b.add_node("human_review", lambda state: {**state, "stage": "awaiting_human_review"})
    b.add_node("publish", lambda state: {**state, "stage": "published"})
    b.set_entry_point("ingest")
    b.add_edge("ingest", "extract")
    b.add_edge("extract", "generate")
    b.add_edge("generate", "validate")
    b.add_edge("validate", "route")
    b.add_conditional_edges(
        "route",
        decide_route,
        {"escalated": END, "review": "human_review", "approved": "publish"},
    )
    b.add_edge("human_review", END)
    b.add_edge("publish", END)
    return b


_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_checkpointer = SqliteSaver(_conn)
app = _build_graph().compile(checkpointer=_checkpointer, interrupt_before=["human_review"])


def run_pipeline(url: str, config: RunConfig) -> PipelineResult:
    """Run the ContentFlow graph for one URL and return a pipeline result."""
    run_id = str(uuid.uuid4())
    start_time = time.time()
    blog_post = BlogPost(url=url)
    llm_info = get_model_info()

    initial_state: ContentFlowState = {
        "run_id": run_id,
        "config": config.model_dump(),
        "blog_post": blog_post.model_dump(),
        "raw_text": None,
        "extraction": None,
        "posts": [],
        "flags": [],
        "validation_result": None,
        "routing_decision": None,
        "error": None,
        "stage": "initialized",
        "start_time": start_time,
        "llm_info": llm_info,
    }
    thread_config = {"configurable": {"thread_id": run_id}}
    result = app.invoke(initial_state, thread_config)
    final_llm_info = result.get("llm_info") or llm_info

    return PipelineResult(
        run_id=result["run_id"],
        status=result.get("routing_decision") or "escalated",
        posts=result.get("posts", []),
        flags=result.get("flags", []),
        raw_extraction=result.get("extraction"),
        duration_seconds=time.time() - result.get("start_time", start_time),
        llm_provider=final_llm_info.get("provider"),
        llm_model=final_llm_info.get("model"),
    )


async def run_pipeline_from_blog_post(
    blog_post: BlogPost, config: RunConfig
) -> PipelineResult:
    """Run the ContentFlow graph using a prepared BlogPost input."""
    run_id = str(uuid.uuid4())
    start_time = time.time()
    llm_info = get_model_info()

    initial_state: ContentFlowState = {
        "run_id": run_id,
        "config": config.model_dump(),
        "blog_post": blog_post.model_dump(),
        "raw_text": blog_post.raw_text,
        "extraction": None,
        "posts": [],
        "flags": [],
        "validation_result": None,
        "routing_decision": None,
        "error": None,
        "stage": "initialized",
        "start_time": start_time,
        "llm_info": llm_info,
    }
    thread_config = {"configurable": {"thread_id": run_id}}

    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        async_app = _build_graph().compile(
            checkpointer=checkpointer, interrupt_before=["human_review"]
        )
        result = await async_app.ainvoke(initial_state, thread_config)

    final_llm_info = result.get("llm_info") or llm_info

    return PipelineResult(
        run_id=result["run_id"],
        status=result.get("routing_decision") or "escalated",
        posts=result.get("posts", []),
        flags=result.get("flags", []),
        raw_extraction=result.get("extraction"),
        duration_seconds=time.time() - result.get("start_time", start_time),
        llm_provider=final_llm_info.get("provider"),
        llm_model=final_llm_info.get("model"),
    )
