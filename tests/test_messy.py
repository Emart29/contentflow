"""Messy input tests for contentflow."""

import json
from pathlib import Path

import pytest

from agent.graph import run_pipeline_from_blog_post
from models.input import BlogPost


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_messy_case(run_config):
    """Run the insufficient-content escalation path."""
    fixture = json.loads((FIXTURES_DIR / "messy_input.json").read_text(encoding="utf-8"))
    blog_post = BlogPost(**fixture)

    result = await run_pipeline_from_blog_post(blog_post, run_config)

    assert result.status == "escalated"
    assert any(flag.reason == "INSUFFICIENT_CONTENT" for flag in result.flags)
    assert len(result.posts) == 0

    print("\n=== MESSY CASE FLAGS ===")
    for flag in result.flags:
        print(f"[{flag.stage}] {flag.reason}: {flag.detail}")

    (FIXTURES_DIR / "output_messy.json").write_text(
        json.dumps(result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
