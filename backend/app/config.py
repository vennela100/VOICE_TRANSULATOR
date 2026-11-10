from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets

_PROCESS_ROOM_TOKEN_SECRET = secrets.token_bytes(32)


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    app_name: str = "BharatVaani Live"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Gnani Prisma STT
    gnani_api_key_id: str = ""
    prisma_endpoint: str = "https://api.vachana.ai/stt/v3"

    # Gnani Timbre TTS
    timbre_endpoint: str = "https://api.vachana.ai/api/v1/tts/inference"
    timbre_hindi_voice: str = "Nalini"
    timbre_telugu_voice: str = "Suhana"

    # Translation
    translation_provider: str = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.5-flash"
    gemini_tts_model: str = "gemini-3.1-flash-tts-preview"

    # Provider selection
    stt_provider: str = "mock"
    tts_provider: str = "mock"

    # Database
    database_url: str = "sqlite:///./bharatvaani.db"

    # Room
    room_expiry_minutes: int = 120
    room_token_secret: str = ""
    cors_allowed_origins: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_room_token_secret() -> bytes:
    """Use configured stable secret, or a per-process secret for local development."""
    configured = get_settings().room_token_secret
    return configured.encode("utf-8") if configured else _PROCESS_ROOM_TOKEN_SECRET
