from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TtsResult:
    """Result from text-to-speech synthesis."""
    audio_bytes: bytes
    audio_format: str = "wav"
    error: Optional[str] = None


class TtsProvider(ABC):
    """Interface for text-to-speech providers."""

    @abstractmethod
    async def synthesize(self, text: str, language: str) -> TtsResult:
        """Synthesize text to audio bytes."""
        pass
