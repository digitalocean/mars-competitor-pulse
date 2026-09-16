"""Harness-native ChatOpenAI factory (Seed 4 pattern).

Prefers HARNESS_INFERENCE_* env vars; falls back to OPENAI_*.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_MODEL = "gpt-4o-mini"


def resolve_llm_env() -> dict[str, str | None]:
    """Resolve base_url, api_key, model from harness env first, then OPENAI_*."""
    base_url = os.environ.get("HARNESS_INFERENCE_BASE_URL") or os.environ.get(
        "OPENAI_BASE_URL"
    )
    api_key = os.environ.get("HARNESS_INFERENCE_API_KEY") or os.environ.get(
        "OPENAI_API_KEY"
    )
    model = (
        os.environ.get("HARNESS_INFERENCE_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or DEFAULT_MODEL
    )
    return {"base_url": base_url, "api_key": api_key, "model": model}


def harness_env_available() -> bool:
    """True when a usable API key is present (harness or OpenAI)."""
    return bool(
        os.environ.get("HARNESS_INFERENCE_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )


def get_llm(**kwargs: Any):
    """Return a ChatOpenAI client wired for MARS harness or local OpenAI-compatible."""
    from langchain_openai import ChatOpenAI

    resolved = resolve_llm_env()
    if not resolved["api_key"]:
        raise RuntimeError(
            "No inference API key set. Export HARNESS_INFERENCE_API_KEY "
            "(preferred) or OPENAI_API_KEY."
        )
    params: dict[str, Any] = {
        "model": resolved["model"],
        "api_key": resolved["api_key"],
    }
    if resolved["base_url"]:
        params["base_url"] = resolved["base_url"]
    params.update(kwargs)
    return ChatOpenAI(**params)
