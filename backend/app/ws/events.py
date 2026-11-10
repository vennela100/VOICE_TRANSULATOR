from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
import uuid


class WSEvent(BaseModel):
    """Base WebSocket event."""
    type: str
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str = ""
    sender_id: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AudioDataEvent(WSEvent):
    type: str = "audio_data"
    audio_base64: str = ""


class TranscriptFinalEvent(WSEvent):
    type: str = "transcript.final"
    text: str = ""
    language: str = ""


class TranslationCompletedEvent(WSEvent):
    type: str = "translation.completed"
    text: str = ""
    source_language: str = ""
    target_language: str = ""


class AudioReadyEvent(WSEvent):
    type: str = "audio.ready"
    audio_base64: str = ""
    audio_format: str = "wav"


class MessageDeliveredEvent(WSEvent):
    type: str = "message.delivered"


class VerificationRequiredEvent(WSEvent):
    type: str = "verification.required"
    prompt_text: str = ""
    entities: list = []


class VerificationConfirmedEvent(WSEvent):
    type: str = "verification.confirmed"


class VerificationRejectedEvent(WSEvent):
    type: str = "verification.rejected"


class ErrorEvent(WSEvent):
    type: str = "error"
    error: str = ""


class ParticipantJoinedEvent(WSEvent):
    type: str = "participant_joined"
    participant_id: str = ""
    name: str = ""
    language: str = ""


class ParticipantLeftEvent(WSEvent):
    type: str = "participant_left"
    participant_id: str = ""
