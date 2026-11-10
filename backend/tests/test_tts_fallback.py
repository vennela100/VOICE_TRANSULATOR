import io
import wave

import pytest

from app.services.tts.fallback import FallbackTtsProvider, _usable_audio
from app.services.tts.provider import TtsResult


def wav_bytes(frames=b"\x00\x00" * 240):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(frames)
    return buffer.getvalue()


class StubTts:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    async def synthesize(self, text, language):
        self.calls += 1
        return self.result


class RaisingTts:
    def __init__(self, error):
        self.error = error
        self.calls = 0

    async def synthesize(self, text, language):
        self.calls += 1
        raise self.error


def test_usable_audio_requires_well_formed_nonempty_wav():
    assert _usable_audio(TtsResult(wav_bytes()))
    assert not _usable_audio(TtsResult(b"not a wav"))
    assert not _usable_audio(TtsResult(b"", error="provider unavailable"))
    assert not _usable_audio(TtsResult(b"not really mp3", audio_format="mp3"))


@pytest.mark.asyncio
async def test_fallback_runs_when_primary_wav_is_invalid():
    primary = StubTts(TtsResult(b"invalid"))
    fallback_audio = wav_bytes()
    fallback = StubTts(TtsResult(fallback_audio))

    result = await FallbackTtsProvider(primary, fallback).synthesize("నమస్కారం", "te")

    assert result.audio_bytes == fallback_audio
    assert result.audio_format == "wav"
    assert primary.calls == fallback.calls == 1


@pytest.mark.asyncio
async def test_unvalidated_primary_format_uses_wav_fallback():
    primary = StubTts(TtsResult(b"invalid mp3", audio_format="mp3"))
    fallback_audio = wav_bytes()
    fallback = StubTts(TtsResult(fallback_audio, audio_format="wav"))

    result = await FallbackTtsProvider(primary, fallback).synthesize("hello", "te")

    assert result.audio_bytes == fallback_audio
    assert result.audio_format == "wav"
    assert primary.calls == fallback.calls == 1


@pytest.mark.asyncio
async def test_valid_primary_audio_does_not_call_fallback():
    primary = StubTts(TtsResult(wav_bytes()))
    fallback = StubTts(TtsResult(b"unused"))

    result = await FallbackTtsProvider(primary, fallback).synthesize("नमस्ते", "hi")

    assert _usable_audio(result)
    assert primary.calls == 1
    assert fallback.calls == 0


@pytest.mark.asyncio
async def test_primary_timeout_invokes_valid_fallback():
    primary = RaisingTts(TimeoutError())
    fallback = StubTts(TtsResult(wav_bytes()))

    result = await FallbackTtsProvider(primary, fallback).synthesize("hello", "te")

    assert _usable_audio(result)
    assert primary.calls == fallback.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_primary_rate_limit_or_service_error_invokes_valid_fallback(status):
    primary = StubTts(TtsResult(b"", error=f"provider returned HTTP {status}"))
    fallback_audio = wav_bytes()
    fallback = StubTts(TtsResult(fallback_audio))

    result = await FallbackTtsProvider(primary, fallback).synthesize("hello", "hi")

    assert result.audio_bytes == fallback_audio
    assert primary.calls == fallback.calls == 1


@pytest.mark.asyncio
async def test_fallback_exception_returns_safe_unavailable_result():
    primary = RaisingTts(TimeoutError())
    fallback = RaisingTts(RuntimeError("sensitive provider response"))

    result = await FallbackTtsProvider(primary, fallback).synthesize("hello", "hi")

    assert result.audio_bytes == b""
    assert result.error == "Primary and fallback speech providers are unavailable"
    assert "sensitive" not in result.error
