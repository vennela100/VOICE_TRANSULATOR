import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey
from app.db.session import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    sender_id = Column(String, ForeignKey("participants.id"), nullable=False)
    original_text = Column(Text, nullable=True)
    original_language = Column(String(5), nullable=True)
    translated_text = Column(Text, nullable=True)
    translated_language = Column(String(5), nullable=True)
    status = Column(String(30), default="recording")
    needs_confirmation = Column(Boolean, default=False)
    confirmed_entities = Column(JSON, nullable=True)
    tts_audio_base64 = Column(Text, nullable=True)
    tts_audio_format = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
