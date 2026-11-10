"""Optional Gemini Hindi/Telugu translation adapter.

The provider is selected only when TRANSLATION_PROVIDER=gemini and a backend
GEMINI_API_KEY is present. It returns machine-readable JSON and never treats a
model confidence score as proof that critical values are correct.
"""

import asyncio
import json
import logging

import httpx

from app.services.translation.provider import TranslationProvider, TranslationResult

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "hi": "Hindi",
    "en": "English",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
}


def _should_try_fallback(error: Exception) -> bool:
    status = getattr(error, "code", None) or getattr(error, "status_code", None)
    return status in {408, 429, 500, 502, 503, 504} or isinstance(
        error, (TimeoutError, ConnectionError, httpx.TransportError)
    )


class GeminiTranslationProvider(TranslationProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.8-flash",
        fallback_model: str = "gemini-3.5-flash",
    ):
        if not api_key:
            raise ValueError("Set GEMINI_API_KEY in backend/.env when TRANSLATION_PROVIDER=gemini")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install backend dependencies to use the Gemini translator") from exc
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=45_000),
        )
        self.model = model
        self.fallback_model = fallback_model

    async def translate(self, text: str, source_language: str, target_language: str) -> TranslationResult:
        source_name = LANG_NAMES.get(source_language, source_language)
        target_name = LANG_NAMES.get(target_language, target_language)
        prompt = f"""Translate the finalized utterance from {source_name} to {target_name}.
Return one JSON object with exactly these string fields: translation, speech_text.
Rules:
- Preserve every number's value, amount, date, time, proper name, and negation.
- Do not invent missing details or add explanations.
- translation is natural written {target_name}, retaining numeric forms when practical.
- speech_text has the same meaning, with amounts, dates and times written in a way a speaker of {target_name} would say them aloud.
- If a phrase is unclear, preserve it faithfully instead of guessing.

Utterance:
{json.dumps(text, ensure_ascii=False)}"""

        try:
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
            except Exception as primary_error:
                if (
                    self.fallback_model == self.model
                    or not _should_try_fallback(primary_error)
                ):
                    raise
                logger.warning(
                    "Gemini model %s unavailable (%s); retrying with %s",
                    self.model,
                    type(primary_error).__name__,
                    self.fallback_model,
                )
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.fallback_model,
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
            payload = json.loads(response.text or "")
            translated = payload.get("translation")
            speech_text = payload.get("speech_text")
            if not isinstance(translated, str) or not translated.strip():
                raise ValueError("translation field was empty or invalid")
            if not isinstance(speech_text, str) or not speech_text.strip():
                raise ValueError("speech_text field was empty or invalid")
            return TranslationResult(
                translated_text=translated.strip(),
                speech_text=speech_text.strip(),
                source_language=source_language,
                target_language=target_language,
            )
        except Exception as exc:
            # Provider errors can include request details. Return a short error
            # to the client and keep credentials and full prompt out of logs.
            logger.warning("Gemini translation request failed (%s)", type(exc).__name__)
            return TranslationResult(
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                error=f"Translation service failed ({type(exc).__name__})",
            )
