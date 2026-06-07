"""Single-command demo runner for ContentFlow."""

import asyncio
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT / "tests" / "fixtures"
ENV_PATH = ROOT / ".env"

PROVIDER_KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "ollama": None,
}


def check_environment() -> bool:
    """Validate local demo environment before importing the graph."""
    if not ENV_PATH.exists():
        print("Missing .env file.")
        print("Create .env in the project root and add your LLM credentials.")
        print("For the default setup, add:")
        print("LLM_PROVIDER=groq")
        print("GROQ_API_KEY=your_key_here")
        print("Free key at console.groq.com")
        return False

    load_dotenv(ENV_PATH)
    provider = os.getenv("LLM_PROVIDER", "groq")
    key_name = PROVIDER_KEY_ENV.get(provider)

    if key_name and not os.getenv(key_name):
        if provider == "groq":
            print("Add your GROQ_API_KEY to .env. Free key at console.groq.com")
        else:
            print(f"Add your {key_name} to .env for LLM_PROVIDER={provider}.")
        return False

    if provider not in PROVIDER_KEY_ENV:
        print(
            f"Unknown LLM_PROVIDER: {provider}. "
            "Valid options: groq, anthropic, openai, gemini, ollama"
        )
        return False

    return True


def load_fixture(name: str) -> dict:
    """Load a JSON fixture by file name."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def save_result(name: str, result) -> None:
    """Save a pipeline result to the fixtures directory."""
    (FIXTURES_DIR / name).write_text(
        json.dumps(result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


async def run_case(label: str, fixture_name: str, output_name: str, config):
    """Run one demo case and return formatted summary data."""
    from agent.graph import run_pipeline_from_blog_post
    from models.input import BlogPost

    blog_post = BlogPost(**load_fixture(fixture_name))
    start = time.perf_counter()
    result = await run_pipeline_from_blog_post(blog_post, config)
    elapsed = time.perf_counter() - start
    save_result(output_name, result)

    input_label = {
        "normal": "live URL fetch",
        "messy": "partial HTML",
        "failure": "sensitive post",
    }[label]

    return {
        "run": label,
        "input": input_label,
        "status": result.status,
        "posts": len(result.posts),
        "flags": len(result.flags),
        "time": elapsed,
    }


def print_table(rows: list[dict]) -> None:
    """Print demo results with rich when available, plain text otherwise."""
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        print("Run       | Input          | Status    | Posts | Flags | Time")
        print("----------|----------------|-----------|-------|-------|-----")
        for row in rows:
            print(
                f"{row['run']:<9} | {row['input']:<14} | {row['status']:<9} | "
                f"{row['posts']:<5} | {row['flags']:<5} | {row['time']:.1f}s"
            )
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Run")
    table.add_column("Input")
    table.add_column("Status")
    table.add_column("Posts", justify="right")
    table.add_column("Flags", justify="right")
    table.add_column("Time", justify="right")

    for row in rows:
        table.add_row(
            row["run"],
            row["input"],
            row["status"],
            str(row["posts"]),
            str(row["flags"]),
            f"{row['time']:.1f}s",
        )

    Console().print(table)


async def main() -> int:
    """Run all demo cases sequentially."""
    if not check_environment():
        return 1

    from agent.llm import get_model_info, get_provider_name
    from models.input import RunConfig

    model_info = get_model_info()
    print(f"ContentFlow Demo — {get_provider_name()} · {model_info['model']}")
    print("-" * 64)

    config = RunConfig(
        client_name="Single Grain",
        brand_voice="Professional and data-driven",
    )

    rows = []
    rows.append(
        await run_case("normal", "normal_input.json", "output_normal.json", config)
    )
    rows.append(await run_case("messy", "messy_input.json", "output_messy.json", config))
    rows.append(
        await run_case("failure", "failure_input.json", "output_failure.json", config)
    )

    print_table(rows)
    print()
    print("Output logs saved to tests/fixtures/")
    print("Demo UI: open ui/index.html (run API first)")
    print("API: docker compose up  OR  uvicorn api.main:app --reload --port 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
