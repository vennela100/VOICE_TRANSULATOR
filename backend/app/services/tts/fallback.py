"""Use a secondary speech service when the primary provider returns no audio."""

import logging
import io
import wave

from app.services.tts.provider import TtsProvider, TtsResult

logger = logging.getLogger(__name__)


def _usable_audio(result: TtsResult) -> bool:
    if result.error or not result.audio_bytes or len(result.audio_bytes) < 44:
        return False
    if result.audio_format != "wav":
        # The live Gnani and Gemini adapters both promise WAV. Unknown
        # containers cannot be validated safely, so let the fallback run.
        return False
    try:
        with wave.open(io.BytesIO(result.audio_bytes), "rb") as audio:
            frame_size = audio.getnchannels() * audio.getsampwidth()
            if frame_size <= 0:
                return False
            nframes = audio.getnframes()
            return (0 < nframes <= len(result.audio_bytes) // frame_size) or (nframes >= 2**30 and len(result.audio_bytes) > 44)
    except (wave.Error, EOFError, OSError):
        return False


class FallbackTtsProvider(TtsProvider):
    def __init__(self, primary: TtsProvider, fallback: TtsProvider):
        self.primary = primary
        self.fallback = fallback

    async def synthesize(self, text: str, language: str) -> TtsResult:
        try:
            result = await self.primary.synthesize(text, language)
        except Exception as exc:
            logger.warning("Primary TTS raised (%s); trying fallback", type(exc).__name__)
            result = TtsResult(b"", audio_format="wav", error=type(exc).__name__)
        if _usable_audio(result):
            return result

        logger.warning("Primary TTS unavailable or returned invalid audio; trying Gemini speech output")
        try:
            fallback_result = await self.fallback.synthesize(text, language)
        except Exception as exc:
            logger.warning("Fallback TTS raised (%s)", type(exc).__name__)
            fallback_result = TtsResult(b"", audio_format="wav", error=type(exc).__name__)
        if _usable_audio(fallback_result):
            return fallback_result
        return TtsResult(
            b"",
            audio_format="wav",
            error="Primary and fallback speech providers are unavailable",
        )
