"""Gnani Prisma v2.5 adapter using the documented REST API."""

import aiohttp

from app.services.stt.provider import SttProvider, SttResult


class GnaniPrismaProvider(SttProvider):
    def __init__(self, api_key_id: str, endpoint: str):
        if not api_key_id:
            raise ValueError(
                "GNANI_API_KEY_ID is required when STT_PROVIDER=gnani. "
                "Set it in backend/.env; do not put it in the frontend."
            )
        self.api_key_id = api_key_id
        self.endpoint = endpoint

    async def transcribe(self, audio_bytes: bytes, language: str) -> SttResult:
        if not audio_bytes:
            return SttResult(text="", language=language, is_empty=True, error="Empty audio")

        language_codes = {
            "hi": "hi-IN",
            "en": "en-IN",
            "te": "te-IN",
            "ta": "ta-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "mr": "mr-IN",
            "bn": "bn-IN",
            "gu": "gu-IN",
            "pa": "pa-IN",
            "or": "or-IN",
            "ur": "ur-IN",
        }
        try:
            language_code = language_codes[language]
        except KeyError as exc:
            raise ValueError(f"Unsupported Prisma language: {language}") from exc

        form = aiohttp.FormData()
        form.add_field(
            "audio_file",
            audio_bytes,
            filename="utterance.wav",
            content_type="audio/wav",
        )
        form.add_field("language_code", language_code)

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.endpoint,
                headers={"X-API-Key-ID": self.api_key_id},
                data=form,
            ) as response:
                try:
                    body = await response.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError):
                    body = {}

                if response.status >= 400:
                    error = body.get("error", {}) if isinstance(body, dict) else {}
                    detail = error.get("message") or f"HTTP {response.status}"
                    # Never include request headers or credentials in raised errors.
                    raise RuntimeError(f"Gnani Prisma STT failed: {detail}")

        transcript = body.get("transcript", "") if isinstance(body, dict) else ""
        if not isinstance(transcript, str):
            raise RuntimeError("Gnani Prisma returned an invalid transcript response")
        return SttResult(
            text=transcript.strip(),
            language=language,
            is_empty=not transcript.strip(),
        )
