"""Failure input tests for contentflow."""

import json
from pathlib import Path

import pytest

from agent.graph import run_pipeline_from_blog_post
from models.input import BlogPost


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_failure_case(run_config):
    """Run the risky-claims escalation or review path."""
    fixture = json.loads((FIXTURES_DIR / "failure_input.json").read_text(encoding="utf-8"))
    blog_post = BlogPost(**fixture)

    result = await run_pipeline_from_blog_post(blog_post, run_config)

    assert result.status in ["escalated", "review"]

    trigger_reasons = [
        "UNVERIFIED_CLAIMS_DETECTED",
        "SENSITIVE_TOPICS_DETECTED",
        "SENSITIVE_TOPICS_PRESENT",
    ]
    assert any(flag.reason in trigger_reasons for flag in result.flags)

    print("\n=== FAILURE CASE FLAGS ===")
    print(f"Status: {result.status}")
    for flag in result.flags:
        print(f"[{flag.stage}] {flag.reason}: {flag.detail}")

    (FIXTURES_DIR / "output_failure.json").write_text(
        json.dumps(result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
