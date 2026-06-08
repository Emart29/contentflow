"""Generate node for the contentflow agent."""

import asyncio
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm
from agent.state import ContentFlowState
from models.output import EscalationFlag, SocialPost


REQUIRED_GENERATION_FIELDS = {"platform", "content", "hashtags", "confidence"}


def _generate_prompt_path() -> Path:
    """Return the path to the generator system prompt."""
    return Path(__file__).resolve().parents[2] / "prompts" / "generate.md"


def _build_user_message(
    platform: str,
    brand_voice: str,
    blocked_terms: list[str],
    extraction: dict,
    extra_instruction: str | None = None,
) -> str:
    """Build a platform-specific generation request."""
    message = (
        f"Platform: {platform}\n"
        f"Brand voice: {brand_voice}\n"
        f"Blocked terms: {blocked_terms}\n"
        f"Extraction data: {json.dumps(extraction)}\n"
        "Instruction: Generate a post for this platform following the system prompt rules."
    )
    if extra_instruction:
        message = f"{message}\n{extra_instruction}"
    return message


async def _invoke_platform(
    llm,
    system_prompt: str,
    platform: str,
    brand_voice: str,
    blocked_terms: list[str],
    extraction: dict,
    extra_instruction: str | None = None,
):
    """Invoke the LLM for one platform."""
    user_message = _build_user_message(
        platform=platform,
        brand_voice=brand_voice,
        blocked_terms=blocked_terms,
        extraction=extraction,
        extra_instruction=extra_instruction,
    )
    return await llm.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
    )


async def generate(state: ContentFlowState) -> dict:
    """Generate social posts for each configured platform."""
    if state.get("routing_decision") == "escalated":
        return {}

    system_prompt = _generate_prompt_path().read_text(encoding="utf-8")
    config = state["config"]
    platforms = config["platforms"]
    brand_voice = config.get("brand_voice", "")
    blocked_terms = config.get("blocked_terms", [])
    extraction = state.get("extraction") or {}
    llm = get_llm()

    responses = await asyncio.gather(
        *[
            _invoke_platform(
                llm=llm,
                system_prompt=system_prompt,
                platform=platform,
                brand_voice=brand_voice,
                blocked_terms=blocked_terms,
                extraction=extraction,
            )
            for platform in platforms
        ],
        return_exceptions=True,
    )

    flags = []
    social_posts = []

    for platform, response in zip(platforms, responses):
        if isinstance(response, Exception):
            flags.append(
                EscalationFlag(
                    reason="GENERATION_ERROR",
                    stage="generate",
                    detail=f"{platform}: {response}",
                ).model_dump()
            )
            continue

        try:
            generated = json.loads(response.content)
        except json.JSONDecodeError:
            flags.append(
                EscalationFlag(
                    reason="GENERATION_PARSE_ERROR",
                    stage="generate",
                    detail=f"{platform}: {response.content[:200]}",
                ).model_dump()
            )
            continue

        missing_fields = sorted(REQUIRED_GENERATION_FIELDS - set(generated))
        if missing_fields:
            flags.append(
                EscalationFlag(
                    reason="GENERATION_INCOMPLETE",
                    stage="generate",
                    detail=f"{platform}: Missing: {missing_fields}",
                ).model_dump()
            )
            continue

        content = generated["content"]

        if platform == "twitter" and len(content) > 270:
            retry_response = await _invoke_platform(
                llm=llm,
                system_prompt=system_prompt,
                platform=platform,
                brand_voice=brand_voice,
                blocked_terms=blocked_terms,
                extraction=extraction,
                extra_instruction=(
                    "IMPORTANT: your response was over 270 characters. "
                    "Rewrite to be strictly under 270 characters."
                ),
            )

            try:
                retry_generated = json.loads(retry_response.content)
            except json.JSONDecodeError:
                flags.append(
                    EscalationFlag(
                        reason="GENERATION_PARSE_ERROR",
                        stage="generate",
                        detail=f"{platform}: {retry_response.content[:200]}",
                    ).model_dump()
                )
            else:
                retry_missing = sorted(REQUIRED_GENERATION_FIELDS - set(retry_generated))
                if not retry_missing:
                    generated = retry_generated
                    content = generated["content"]

            if len(content) > 270:
                generated["content"] = f"{content[:267]}..."
                content = generated["content"]
                flags.append(
                    EscalationFlag(
                        reason="TWITTER_TRUNCATED",
                        stage="generate",
                        detail="twitter: Content exceeded 270 characters after retry",
                    ).model_dump()
                )

        try:
            social_posts.append(
                SocialPost(
                    platform=platform,
                    content=content,
                    char_count=len(content),
                    hashtags=generated["hashtags"],
                    confidence=generated["confidence"],
                )
            )
        except ValueError as exc:
            flags.append(
                EscalationFlag(
                    reason="GENERATION_VALIDATION_ERROR",
                    stage="generate",
                    detail=f"{platform}: {exc}",
                ).model_dump()
            )

    update = {
        "posts": [post.model_dump() for post in social_posts],
        "flags": flags,
        "stage": "generate_complete",
    }

    if not social_posts:
        update["flags"] = [
            *flags,
            EscalationFlag(
                reason="ALL_GENERATION_FAILED",
                stage="generate",
                detail="No platforms generated a valid post",
            ).model_dump(),
        ]
        update["routing_decision"] = "escalated"

    return update
