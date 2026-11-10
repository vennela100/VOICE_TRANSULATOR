import uuid
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean
from app.db.session import Base


def generate_room_code() -> str:
    """Generate a uniformly random six-character alphanumeric room code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(6), unique=True, index=True, nullable=False, default=generate_room_code)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=120))
    is_active = Column(Boolean, default=True)
