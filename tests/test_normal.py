"""Normal input tests for contentflow."""

import json
from pathlib import Path

import pytest

from agent.graph import run_pipeline_from_blog_post
from models.input import BlogPost


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_normal_case(run_config):
    """Run the happy path against a live URL."""
    fixture = json.loads((FIXTURES_DIR / "normal_input.json").read_text(encoding="utf-8"))
    blog_post = BlogPost(**fixture)

    result = await run_pipeline_from_blog_post(blog_post, run_config)

    assert result.status == "approved"
    assert len(result.posts) == 3

    linkedin = next(post for post in result.posts if post.platform == "linkedin")
    twitter = next(post for post in result.posts if post.platform == "twitter")

    assert linkedin.char_count <= 1300
    assert twitter.char_count <= 270

    hard_flag_reasons = [
        "BLOCKED_TERM_DETECTED",
        "UNVERIFIED_CLAIMS_DETECTED",
        "FIRST_PERSON_DETECTED",
    ]
    assert not any(flag.reason in hard_flag_reasons for flag in result.flags)

    print("\n=== NORMAL CASE OUTPUT ===")
    for post in result.posts:
        print(
            f"\n[{post.platform.upper()}] "
            f"({post.char_count} chars, confidence: {post.confidence})"
        )
        print(post.content)
        if post.hashtags:
            print("Hashtags:", " ".join(post.hashtags))

    (FIXTURES_DIR / "output_normal.json").write_text(
        json.dumps(result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
