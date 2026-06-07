"""LLM helpers for the contentflow agent."""

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def get_provider_name() -> str:
    """Return the configured LLM provider name."""
    return os.getenv("LLM_PROVIDER", "groq")


def get_llm() -> Any:
    """Create a chat model instance for the configured LLM provider."""
    provider = get_provider_name()
    override = os.getenv("LLM_MODEL_OVERRIDE")

    if provider == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY not set. Get a free key at console.groq.com")
        from langchain_groq import ChatGroq

        model = override or "llama-3.3-70b-versatile"
        return ChatGroq(model=model, temperature=0)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        model = override or "claude-sonnet-4-20250514"
        return ChatAnthropic(model=model, temperature=0)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model = override or "gpt-4o"
        return ChatOpenAI(model=model, temperature=0)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = override or "gemini-2.0-flash"
        return ChatGoogleGenerativeAI(model=model, temperature=0)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = os.getenv("OLLAMA_MODEL", "llama3.3")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model, base_url=base_url)

    raise ValueError(
        f"Unknown LLM_PROVIDER: {provider}. "
        "Valid options: groq, anthropic, openai, gemini, ollama"
    )


def get_model_info() -> dict:
    """Return the configured provider and resolved model name."""
    provider = get_provider_name()

    try:
        llm = get_llm()
    except ImportError:
        return {"provider": provider, "model": "unknown"}

    model = (
        getattr(llm, "model_name", None)
        or getattr(llm, "model", None)
        or getattr(llm, "model_id", None)
        or "unknown"
    )
    return {"provider": provider, "model": str(model)}
