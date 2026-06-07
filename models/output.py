"""Output models for contentflow."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class SocialPost(BaseModel):
    """Generated social post for a specific publishing platform."""

    platform: Literal["linkedin", "twitter", "instagram"]
    content: str
    char_count: int
    hashtags: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        """Validate that generated content is not blank."""
        if not value.strip():
            raise ValueError("content must not be blank")
        return value

    @field_validator("char_count")
    @classmethod
    def char_count_must_not_be_negative(cls, value: int) -> int:
        """Validate that character count is not negative."""
        if value < 0:
            raise ValueError("char_count must be greater than or equal to 0")
        return value

    @field_validator("hashtags")
    @classmethod
    def hashtags_must_not_be_blank(cls, value: list[str]) -> list[str]:
        """Validate hashtags when provided."""
        if any(not hashtag.strip() for hashtag in value):
            raise ValueError("hashtags must not contain blank values")
        return value

    @model_validator(mode="after")
    def char_count_must_match_content(self) -> "SocialPost":
        """Validate that char_count matches the content length."""
        if self.char_count != len(self.content):
            raise ValueError("char_count must match content length")
        return self


class EscalationFlag(BaseModel):
    """Reason and context for a pipeline escalation."""

    reason: str
    stage: str
    detail: str

    @field_validator("reason", "stage", "detail")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        """Validate escalation text fields."""
        if not value.strip():
            raise ValueError("escalation fields must not be blank")
        return value


class PipelineResult(BaseModel):
    """Final pipeline result including posts, flags, and execution metadata."""

    run_id: str
    status: Literal["approved", "review", "escalated"]
    posts: list[SocialPost] = Field(default_factory=list)
    flags: list[EscalationFlag] = Field(default_factory=list)
    raw_extraction: dict | None = None
    duration_seconds: float | None = None
    llm_provider: str | None = None
    llm_model: str | None = None

    @field_validator("run_id")
    @classmethod
    def run_id_must_not_be_blank(cls, value: str) -> str:
        """Validate that the run identifier is not blank."""
        if not value.strip():
            raise ValueError("run_id must not be blank")
        return value

    @field_validator("duration_seconds")
    @classmethod
    def duration_must_not_be_negative(cls, value: float | None) -> float | None:
        """Validate that duration is not negative."""
        if value is not None and value < 0:
            raise ValueError("duration_seconds must be greater than or equal to 0")
        return value

    @field_validator("llm_provider", "llm_model")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        """Validate optional text metadata when provided."""
        if value is not None and not value.strip():
            raise ValueError("optional text fields must not be blank when provided")
        return value
