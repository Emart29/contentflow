"""Run ContentFlow against real Single Grain URLs and save observed results."""

import asyncio
import json
import time
from pathlib import Path

from agent.graph import run_pipeline_from_blog_post
from models.input import BlogPost, RunConfig


ROOT = Path(__file__).resolve().parents[1]
BATCH_RESULTS_JSON = ROOT / "scripts" / "batch_results.json"
BATCH_RESULTS_MD = ROOT / "BATCH_TEST_RESULTS.md"

URLS = [
    "https://www.singlegrain.com/blog/ms/chatgpt-marketing/",
    "https://www.singlegrain.com/blog/ms/ai-seo/",
    "https://www.singlegrain.com/blog/ms/content-marketing/",
    "https://www.singlegrain.com/blog/ms/social-media-marketing/",
    "https://www.singlegrain.com/blog/ms/email-marketing/",
]

CONFIG = RunConfig(
    client_name="Single Grain",
    brand_voice="Data-driven, direct, results-focused. Uses specific numbers. Never fluff.",
    platforms=["linkedin", "twitter", "instagram"],
)


def truncate_url(url: str) -> str:
    """Return a compact URL label for markdown tables."""
    trimmed = url.rstrip("/")
    suffix = trimmed.rsplit("/", 1)[-1]
    return f".../{suffix}"


def platform_chars(result, platform: str) -> int:
    """Return character count for a generated platform post."""
    for post in result.posts:
        if post.platform == platform:
            return post.char_count
    return 0


def confidences(result) -> list[str]:
    """Return all generated post confidence labels."""
    return [post.confidence for post in result.posts]


def row_from_result(index: int, url: str, result, elapsed: float) -> dict:
    """Build a serializable batch result row."""
    return {
        "index": index,
        "url": url,
        "url_truncated": truncate_url(url),
        "status": result.status,
        "posts_generated": len(result.posts),
        "flags_count": len(result.flags),
        "linkedin_chars": platform_chars(result, "linkedin"),
        "twitter_chars": platform_chars(result, "twitter"),
        "instagram_chars": platform_chars(result, "instagram"),
        "all_confidences": confidences(result),
        "duration_seconds": result.duration_seconds or elapsed,
        "llm_provider": result.llm_provider,
        "result": result.model_dump(mode="json"),
    }


def markdown_table(rows: list[dict]) -> str:
    """Render batch rows as a markdown table."""
    lines = [
        "# Batch Test Results",
        "",
        "Observed outputs from real Single Grain URLs, real model calls, and live pipeline execution.",
        "",
        "| # | URL (truncated) | Status | LI chars | TW chars | IG chars | Flags | Time |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            "| {index} | {url_truncated} | {status} | {linkedin_chars} | "
            "{twitter_chars} | {instagram_chars} | {flags_count} | {time:.1f}s |".format(
                time=row["duration_seconds"],
                **row,
            )
        )

    lines.append("")
    return "\n".join(lines)


async def main() -> int:
    """Run all batch URLs sequentially and save outputs."""
    rows = []

    for index, url in enumerate(URLS, start=1):
        print(f"[{index}/{len(URLS)}] Running {url}")
        start = time.perf_counter()
        result = await run_pipeline_from_blog_post(BlogPost(url=url), CONFIG)
        elapsed = time.perf_counter() - start
        row = row_from_result(index, url, result, elapsed)
        rows.append(row)
        print(
            f"  status={row['status']} posts={row['posts_generated']} "
            f"flags={row['flags_count']} time={row['duration_seconds']:.1f}s"
        )

    BATCH_RESULTS_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    table = markdown_table(rows)
    BATCH_RESULTS_MD.write_text(table, encoding="utf-8")
    print()
    print(table)
    print(f"Saved full outputs to {BATCH_RESULTS_JSON}")
    print(f"Saved markdown table to {BATCH_RESULTS_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
