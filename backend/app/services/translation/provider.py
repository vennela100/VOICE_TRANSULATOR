from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TranslationResult:
    """Result from translation."""
    translated_text: str
    source_language: str
    target_language: str
    error: Optional[str] = None
    speech_text: Optional[str] = None


class TranslationProvider(ABC):
    """Interface for translation providers."""

    @abstractmethod
    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> TranslationResult:
        """Translate text between languages."""
        pass
