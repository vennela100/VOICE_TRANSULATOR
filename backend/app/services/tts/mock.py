import struct
from app.services.tts.provider import TtsProvider, TtsResult


class MockTtsProvider(TtsProvider):
    """Mock TTS provider. Returns a minimal valid WAV file (1s silence)."""

    async def synthesize(self, text: str, language: str) -> TtsResult:
        sample_rate = 16000
        num_samples = sample_rate  # 1 second of silence
        data_size = num_samples * 2  # 16-bit samples

        wav = bytearray()
        wav.extend(b"RIFF")
        wav.extend(struct.pack("<I", 36 + data_size))
        wav.extend(b"WAVE")
        wav.extend(b"fmt ")
        wav.extend(struct.pack("<I", 16))    # chunk size
        wav.extend(struct.pack("<H", 1))     # PCM format
        wav.extend(struct.pack("<H", 1))     # mono
        wav.extend(struct.pack("<I", sample_rate))
        wav.extend(struct.pack("<I", sample_rate * 2))
        wav.extend(struct.pack("<H", 2))     # block align
        wav.extend(struct.pack("<H", 16))    # bits per sample
        wav.extend(b"data")
        wav.extend(struct.pack("<I", data_size))
        wav.extend(b"\x00" * data_size)

        return TtsResult(audio_bytes=bytes(wav), audio_format="wav")
