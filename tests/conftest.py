"""Pytest configuration for contentflow."""

import os

import pytest
from dotenv import load_dotenv

from models.input import RunConfig


def pytest_configure(config):
    """Configure pytest-asyncio mode for async tests."""
    config.option.asyncio_mode = "auto"


load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")


@pytest.fixture
def run_config() -> RunConfig:
    """Return a default pipeline run configuration for tests."""
    return RunConfig(
        client_name="Test Client",
        brand_voice="Professional and data-driven",
    )
