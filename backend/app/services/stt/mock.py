import random
from app.services.stt.provider import SttProvider, SttResult

MOCK_HINDI_PHRASES = [
    "नमस्ते, मैं ठीक हूँ",
    "सवा लाख रुपये भेज दीजिए",
    "कल दोपहर दो बजे मिलते हैं",
    "पचास हजार रुपये चाहिए",
    "मुझे तीन किलो चावल चाहिए",
    "ढाई हजार रुपये दे दो",
    "पौने दो लाख का सामान आया है",
]

MOCK_TELUGU_PHRASES = [
    "నమస్కారం, నేను బాగున్నాను",
    "లక్ష ఇరవై ఐదు వేలు పంపండి",
    "రేపు మధ్యాహ్నం రెండు గంటలకు కలుద్దాం",
    "యాభై వేల రూపాయలు కావాలి",
    "నాకు మూడు కిలోల బియ్యం కావాలి",
]


class MockSttProvider(SttProvider):
    """Mock STT provider for development. Returns random Hindi/Telugu phrases."""

    async def transcribe(self, audio_bytes: bytes, language: str) -> SttResult:
        if len(audio_bytes) < 100:
            return SttResult(
                text="", language=language, is_empty=True,
                error="Audio too short",
            )

        phrases = MOCK_HINDI_PHRASES if language == "hi" else MOCK_TELUGU_PHRASES
        text = random.choice(phrases)

        return SttResult(text=text, language=language, confidence=0.92)
