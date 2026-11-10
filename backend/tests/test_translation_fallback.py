import asyncio
import json
from types import SimpleNamespace

import pytest

from app.services.translation.gemini_translate import GeminiTranslationProvider


class ProviderError(Exception):
    def __init__(self, code):
        self.code = code


class FakeModels:
    def __init__(self, primary_error=None, fallback_error=None):
        self.primary_error = primary_error
        self.fallback_error = fallback_error
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append(model)
        if model == "primary" and self.primary_error:
            raise self.primary_error
        if model == "fallback" and self.fallback_error:
            raise self.fallback_error
        return SimpleNamespace(text=json.dumps({
            "translation": "నమస్కారం",
            "speech_text": "నమస్కారం",
        }))


def provider_with_models(models):
    provider = object.__new__(GeminiTranslationProvider)
    provider.client = SimpleNamespace(models=models)
    provider.model = "primary"
    provider.fallback_model = "fallback"
    return provider


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_retryable_primary_status_uses_fallback_model(status):
    models = FakeModels(primary_error=ProviderError(status))
    provider = provider_with_models(models)

    result = asyncio.run(provider.translate("नमस्ते", "hi", "te"))

    assert result.translated_text == "నమస్కారం"
    assert result.error is None
    assert models.calls == ["primary", "fallback"]


def test_non_retryable_primary_error_does_not_call_fallback():
    models = FakeModels(primary_error=ProviderError(400))
    provider = provider_with_models(models)

    result = asyncio.run(provider.translate("नमस्ते", "hi", "te"))

    assert result.translated_text == ""
    assert result.error == "Translation service failed (ProviderError)"
    assert models.calls == ["primary"]


@pytest.mark.parametrize("error", [TimeoutError("timed out"), ConnectionError("disconnected")])
def test_primary_network_failure_uses_fallback_model(error):
    models = FakeModels(primary_error=error)
    provider = provider_with_models(models)

    result = asyncio.run(provider.translate("नमस्ते", "hi", "te"))

    assert result.error is None
    assert result.translated_text
    assert models.calls == ["primary", "fallback"]


def test_primary_httpx_timeout_uses_fallback_model():
    import httpx

    models = FakeModels(primary_error=httpx.ReadTimeout("timed out"))
    provider = provider_with_models(models)

    result = asyncio.run(provider.translate("नमस्ते", "hi", "te"))

    assert result.error is None
    assert result.translated_text
    assert models.calls == ["primary", "fallback"]


def test_fallback_timeout_returns_safe_error_without_raising():
    models = FakeModels(
        primary_error=ProviderError(503),
        fallback_error=TimeoutError("private request details"),
    )
    provider = provider_with_models(models)

    result = asyncio.run(provider.translate("नमस्ते", "hi", "te"))

    assert result.translated_text == ""
    assert result.error == "Translation service failed (TimeoutError)"
    assert "private request details" not in result.error
    assert models.calls == ["primary", "fallback"]
