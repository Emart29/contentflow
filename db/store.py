"""Storage helpers for contentflow."""

import json
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from models.output import PipelineResult


DATABASE_URL = "sqlite:///contentflow.db"
engine = create_engine(DATABASE_URL)


class RunLog(SQLModel, table=True):
    """Database record for a completed ContentFlow pipeline run."""

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str
    url: str
    client_name: str
    status: str
    duration_seconds: Optional[float]
    posts_generated: int
    flags_count: int
    flags_detail: str
    posts_detail: str
    llm_provider: Optional[str]
    llm_model: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


def init_db() -> None:
    """Create the SQLite database and run log table if needed."""
    SQLModel.metadata.create_all(engine)


def log_run(result: PipelineResult, url: str, client_name: str) -> RunLog:
    """Save a pipeline result and return the persisted run log."""
    result_data = result.model_dump()
    run_log = RunLog(
        run_id=result.run_id,
        url=url,
        client_name=client_name,
        status=result.status,
        duration_seconds=result.duration_seconds,
        posts_generated=len(result.posts),
        flags_count=len(result.flags),
        flags_detail=json.dumps(result_data["flags"]),
        posts_detail=json.dumps(result_data["posts"]),
        llm_provider=result.llm_provider,
        llm_model=result.llm_model,
    )

    with Session(engine) as session:
        session.add(run_log)
        session.commit()
        session.refresh(run_log)
        return run_log


def get_run(run_id: str) -> RunLog | None:
    """Return a single run log by run identifier."""
    with Session(engine) as session:
        statement = select(RunLog).where(RunLog.run_id == run_id)
        return session.exec(statement).first()


def get_recent_runs(limit: int = 20) -> list[RunLog]:
    """Return recent run logs ordered by creation time descending."""
    with Session(engine) as session:
        statement = select(RunLog).order_by(RunLog.created_at.desc()).limit(limit)
        return list(session.exec(statement).all())


init_db()
