"""Input models for contentflow."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class BlogPost(BaseModel):
    """Input blog post content and source metadata for a pipeline run."""

    url: str
    raw_html: str | None = None
    raw_text: str | None = None
    word_count: int | None = None
    source_label: Literal["observed", "estimated", "benchmarked", "assumed"] = "observed"

    @field_validator("url")
    @classmethod
    def url_must_not_be_blank(cls, value: str) -> str:
        """Validate that the blog post URL is not blank."""
        if not value.strip():
            raise ValueError("url must not be blank")
        return value

    @field_validator("raw_html", "raw_text")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        """Validate optional text fields when provided."""
        if value is not None and not value.strip():
            raise ValueError("text fields must not be blank when provided")
        return value

    @field_validator("word_count")
    @classmethod
    def word_count_must_not_be_negative(cls, value: int | None) -> int | None:
        """Validate that word count is not negative."""
        if value is not None and value < 0:
            raise ValueError("word_count must be greater than or equal to 0")
        return value


class RunConfig(BaseModel):
    """Configuration for generating social content for a client."""

    client_name: str
    brand_voice: str
    blocked_terms: list[str] = Field(default_factory=list)
    platforms: list[Literal["linkedin", "twitter", "instagram"]] = Field(
        default_factory=lambda: ["linkedin", "twitter", "instagram"]
    )
    require_human_review: bool = False

    @field_validator("client_name", "brand_voice")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        """Validate required text fields."""
        if not value.strip():
            raise ValueError("required text fields must not be blank")
        return value

    @field_validator("blocked_terms")
    @classmethod
    def blocked_terms_must_not_be_blank(cls, value: list[str]) -> list[str]:
        """Validate blocked terms when provided."""
        if any(not term.strip() for term in value):
            raise ValueError("blocked_terms must not contain blank values")
        return value

    @field_validator("platforms")
    @classmethod
    def platforms_must_not_be_empty(
        cls, value: list[Literal["linkedin", "twitter", "instagram"]]
    ) -> list[Literal["linkedin", "twitter", "instagram"]]:
        """Validate that at least one target platform is configured."""
        if not value:
            raise ValueError("platforms must contain at least one platform")
        return value

    @model_validator(mode="after")
    def platforms_must_be_unique(self) -> "RunConfig":
        """Validate that each platform appears only once."""
        if len(set(self.platforms)) != len(self.platforms):
            raise ValueError("platforms must not contain duplicates")
        return self
