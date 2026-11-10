"""gTTS-based text-to-speech provider.

Uses Google Text-to-Speech (gTTS) — free, no API key needed.
Generates real spoken audio in Hindi and Telugu.
Output: MP3 format (widely supported by browsers).

Language codes: 'hi' (Hindi), 'te' (Telugu)
"""
import io
import logging
from app.services.tts.provider import TtsProvider, TtsResult

logger = logging.getLogger(__name__)

LANG_MAP = {
    "hi": "hi",
    "te": "te",
}


class GttsTtsProvider(TtsProvider):
    """TTS using gTTS (Google Text-to-Speech, free)."""

    async def synthesize(self, text: str, language: str) -> TtsResult:
        try:
            from gtts import gTTS
            import asyncio

            lang_code = LANG_MAP.get(language, language)

            # gTTS is synchronous, run in thread
            loop = asyncio.get_event_loop()

            def _generate():
                tts = gTTS(text=text, lang=lang_code, slow=False)
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                return buf.read()

            audio_bytes = await loop.run_in_executor(None, _generate)

            logger.info(
                f"gTTS synthesized ({language}): '{text[:40]}' -> {len(audio_bytes)} bytes MP3"
            )

            return TtsResult(
                audio_bytes=audio_bytes,
                audio_format="mp3",
            )

        except ImportError:
            logger.error("gTTS not installed. Run: pip install gTTS")
            return TtsResult(
                audio_bytes=b"",
                audio_format="mp3",
                error="gTTS not installed",
            )
        except Exception as e:
            logger.exception(f"gTTS synthesis failed: {e}")
            return TtsResult(
                audio_bytes=b"",
                audio_format="mp3",
                error=str(e),
            )
