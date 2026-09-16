"""LLM env resolution: harness wins over OPENAI_*; fallback works."""

from __future__ import annotations

import competitor_pulse.llm as llm_mod


def test_harness_env_wins_over_openai(monkeypatch):
    monkeypatch.setenv("HARNESS_INFERENCE_BASE_URL", "https://harness.example/v1")
    monkeypatch.setenv("HARNESS_INFERENCE_MODEL", "harness-model")
    monkeypatch.setenv("HARNESS_INFERENCE_API_KEY", "harness-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "openai-model")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    resolved = llm_mod.resolve_llm_env()
    assert resolved["base_url"] == "https://harness.example/v1"
    assert resolved["model"] == "harness-model"
    assert resolved["api_key"] == "harness-key"


def test_openai_fallback_when_harness_unset(monkeypatch):
    monkeypatch.delenv("HARNESS_INFERENCE_BASE_URL", raising=False)
    monkeypatch.delenv("HARNESS_INFERENCE_MODEL", raising=False)
    monkeypatch.delenv("HARNESS_INFERENCE_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    resolved = llm_mod.resolve_llm_env()
    assert resolved["base_url"] == "https://openai.example/v1"
    assert resolved["model"] == "gpt-test"
    assert resolved["api_key"] == "openai-key"


def test_default_model_when_only_key(monkeypatch):
    monkeypatch.delenv("HARNESS_INFERENCE_BASE_URL", raising=False)
    monkeypatch.delenv("HARNESS_INFERENCE_MODEL", raising=False)
    monkeypatch.delenv("HARNESS_INFERENCE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "only-key")

    resolved = llm_mod.resolve_llm_env()
    assert resolved["api_key"] == "only-key"
    assert resolved["model"] == llm_mod.DEFAULT_MODEL
    assert resolved["base_url"] is None


def test_get_llm_uses_harness(monkeypatch):
    monkeypatch.setenv("HARNESS_INFERENCE_BASE_URL", "https://harness.example/v1")
    monkeypatch.setenv("HARNESS_INFERENCE_MODEL", "harness-model")
    monkeypatch.setenv("HARNESS_INFERENCE_API_KEY", "harness-key")

    client = llm_mod.get_llm()
    model = getattr(client, "model_name", None) or getattr(client, "model", None)
    assert model == "harness-model"
