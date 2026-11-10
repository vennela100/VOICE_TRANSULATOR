"""Google Translate provider using googletrans (free, no API key needed).

This is a reliable translation provider for Hindi <-> Telugu.
Falls back gracefully with error messages.

Language codes: 'hi' (Hindi), 'te' (Telugu)
"""
import logging
from app.services.translation.provider import TranslationProvider, TranslationResult

logger = logging.getLogger(__name__)

# googletrans uses Google's free translation endpoint
# Language code mapping: our codes match googletrans codes exactly
LANG_MAP = {
    "hi": "hi",
    "te": "te",
}


class GoogleTranslateProvider(TranslationProvider):
    """Translation using googletrans (free Google Translate wrapper)."""

    def __init__(self):
        try:
            from googletrans import Translator
            self._translator = Translator()
            logger.info("GoogleTranslateProvider initialized")
        except ImportError:
            logger.error("googletrans not installed. Run: pip install googletrans==4.0.0-rc.1")
            self._translator = None

    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> TranslationResult:
        if not self._translator:
            return TranslationResult(
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                error="googletrans not installed",
            )

        try:
            src = LANG_MAP.get(source_language, source_language)
            dest = LANG_MAP.get(target_language, target_language)

            # googletrans is synchronous, run in thread
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._translator.translate(text, src=src, dest=dest)
            )

            translated = result.text
            logger.info(
                f"Translated ({source_language}->{target_language}): "
                f"'{text[:50]}' -> '{translated[:50]}'"
            )

            return TranslationResult(
                translated_text=translated,
                source_language=source_language,
                target_language=target_language,
            )

        except Exception as e:
            logger.exception(f"Translation failed: {e}")
            return TranslationResult(
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                error=str(e),
            )
