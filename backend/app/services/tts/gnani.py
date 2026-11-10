"""Gnani Timbre v2.5 synchronous REST adapter."""

import logging
import struct

import aiohttp

from app.services.tts.provider import TtsProvider, TtsResult

logger = logging.getLogger(__name__)


def fix_wav_header(audio_bytes: bytes) -> bytes:
    """Normalize streaming WAV headers (e.g. 0xFFFFFFFF sizes) to exact byte lengths."""
    if len(audio_bytes) < 44 or not audio_bytes.startswith(b"RIFF") or audio_bytes[8:12] != b"WAVE":
        return audio_bytes
    b = bytearray(audio_bytes)
    riff_size = len(b) - 8
    struct.pack_into("<I", b, 4, riff_size)
    pos = 12
    while pos < len(b) - 8:
        if b[pos:pos + 4] == b"data":
            data_size = len(b) - (pos + 8)
            struct.pack_into("<I", b, pos + 4, data_size)
            break
        chunk_size = struct.unpack("<I", b[pos + 4:pos + 8])[0]
        pos += 8 + chunk_size
    return bytes(b)


DEFAULT_VOICES = {
    "hi": "Nalini",
    "en": "Kaveri",
    "te": "Suhana",
    "ta": "Kaveri",
    "kn": "Pranav",
    "ml": "Pranav",
    "mr": "Pranav",
    "bn": "Pranav",
    "gu": "Pranav",
    "pa": "Pranav",
    "or": "Pranav",
    "ur": "Pranav",
}

LANGUAGE_CODES = {
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


class GnaniTimbreProvider(TtsProvider):
    def __init__(
        self,
        api_key_id: str,
        endpoint: str,
        hindi_voice: str = "Nalini",
        telugu_voice: str = "Suhana",
    ):
        if not api_key_id:
            raise ValueError("GNANI_API_KEY_ID is required when TTS_PROVIDER=gnani")
        self.api_key_id = api_key_id
        self.endpoint = endpoint
        self.voices = dict(DEFAULT_VOICES)
        self.voices["hi"] = hindi_voice
        self.voices["te"] = telugu_voice

    async def synthesize(self, text: str, language: str) -> TtsResult:
        if language not in LANGUAGE_CODES:
            return TtsResult(b"", audio_format="wav", error=f"Unsupported Timbre language: {language}")
        voice = self.voices.get(language, DEFAULT_VOICES.get(language, "Pranav"))
        payload = {
            "text": text,
            "voice": voice,
            "model": "timbre-v2.5",
            "language": LANGUAGE_CODES[language],
            "speed": 1.0,
            "audio_config": {
                "sample_rate": 48000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }
        timeout = aiohttp.ClientTimeout(total=60)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.endpoint,
                    headers={"X-API-Key-ID": self.api_key_id},
                    json=payload,
                ) as response:
                    content = await response.read()
                    if response.status >= 400:
                        logger.warning("Timbre request failed with HTTP %s", response.status)
                        return TtsResult(b"", audio_format="wav", error=f"TTS service returned HTTP {response.status}")
                    if not content:
                        return TtsResult(b"", audio_format="wav", error="TTS service returned empty audio")
                    return TtsResult(fix_wav_header(content), audio_format="wav")
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("Timbre request failed (%s)", type(exc).__name__)
            return TtsResult(b"", audio_format="wav", error=f"TTS request failed ({type(exc).__name__})")
