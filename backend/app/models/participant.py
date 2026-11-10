import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from app.db.session import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    name = Column(String, nullable=False)
    language = Column(String(5), nullable=False)  # "hi" or "te"
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_connected = Column(Boolean, default=True)
