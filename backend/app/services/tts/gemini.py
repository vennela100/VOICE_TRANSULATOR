"""Gemini text-to-speech fallback using 24 kHz mono PCM output."""

import asyncio
import io
import logging
import wave

from app.services.tts.provider import TtsProvider, TtsResult

logger = logging.getLogger(__name__)


class GeminiTtsProvider(TtsProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-tts-preview"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini TTS")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install backend dependencies to use Gemini TTS") from exc

        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta", timeout=45000))
        self.model = model
        self.types = types

    async def synthesize(self, text: str, language: str) -> TtsResult:
        language_names = {
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
        language_name = language_names.get(language)
        if not language_name:
            return TtsResult(b"", error=f"Unsupported Gemini TTS language: {language}")

        prompt = f"Speak the following {language_name} text exactly. Do not translate or add words:\n{text}"
        config = self.types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=self.types.SpeechConfig(
                voice_config=self.types.VoiceConfig(
                    prebuilt_voice_config=self.types.PrebuiltVoiceConfig(voice_name="Kore")
                )
            ),
        )
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=config,
            )
            parts = response.candidates[0].content.parts
            audio_part = next((part.inline_data for part in parts if part.inline_data), None)
            if not audio_part or not audio_part.data:
                return TtsResult(b"", error="Gemini TTS returned no audio")

            pcm = audio_part.data
            if isinstance(pcm, str):
                import base64

                pcm = base64.b64decode(pcm)
            if pcm.startswith(b"RIFF"):
                return TtsResult(pcm, audio_format="wav")

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm)
            return TtsResult(wav_buffer.getvalue(), audio_format="wav")
        except Exception as exc:
            logger.warning("Gemini TTS request failed (%s)", type(exc).__name__)
            return TtsResult(b"", error=f"Gemini TTS request failed ({type(exc).__name__})")
