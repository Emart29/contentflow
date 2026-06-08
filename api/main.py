"""API entrypoint for contentflow."""

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.graph import run_pipeline_from_blog_post
from models.input import BlogPost
from agent.llm import get_model_info, get_provider_name
from db.store import RunLog, get_recent_runs, get_run, init_db, log_run
from models.input import RunConfig
from models.output import PipelineResult


class RunRequest(BaseModel):
    """Request body for starting a ContentFlow pipeline run."""

    url: str
    client_name: str
    brand_voice: str
    platforms: list[Literal["linkedin", "twitter", "instagram"]] = Field(
        default_factory=lambda: ["linkedin", "twitter", "instagram"]
    )
    blocked_terms: list[str] = Field(default_factory=list)
    require_human_review: bool = False


app = FastAPI(title="ContentFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    """Initialize the database when the API starts."""
    init_db()


@app.post("/run", response_model=PipelineResult, status_code=200)
async def run(request: RunRequest) -> PipelineResult:
    """Run the ContentFlow pipeline for a URL."""
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="url must start with http:// or https://")

    try:
        config = RunConfig(
            client_name=request.client_name,
            brand_voice=request.brand_voice,
            blocked_terms=request.blocked_terms,
            platforms=request.platforms,
            require_human_review=request.require_human_review,
        )
        result = await run_pipeline_from_blog_post(BlogPost(url=request.url), config)
        log_run(result, request.url, request.client_name)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": str(exc)}) from exc


@app.get("/runs", response_model=list[RunLog], status_code=200)
def runs(limit: int = Query(default=20, ge=1, le=100)) -> list[RunLog]:
    """Return recent pipeline run logs."""
    try:
        return get_recent_runs(limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": str(exc)}) from exc


@app.get("/runs/{run_id}", response_model=RunLog, status_code=200)
def run_detail(run_id: str) -> RunLog:
    """Return one pipeline run log."""
    try:
        run_log = get_run(run_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": str(exc)}) from exc

    if run_log is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_log


@app.get("/health", status_code=200)
def health() -> dict:
    """Return API health and LLM configuration metadata."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "llm_provider": get_provider_name(),
        "llm_model": get_model_info()["model"],
    }
