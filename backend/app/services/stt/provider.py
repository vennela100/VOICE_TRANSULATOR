from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SttResult:
    """Result from speech-to-text transcription."""
    text: str
    language: str
    confidence: Optional[float] = None
    is_empty: bool = False
    error: Optional[str] = None


class SttProvider(ABC):
    """Interface for speech-to-text providers."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str) -> SttResult:
        """Transcribe audio bytes to text."""
        pass
