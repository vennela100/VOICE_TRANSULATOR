from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String

from app.db.session import Base


class JoinAttempt(Base):
    __tablename__ = "join_attempts"
    __table_args__ = (Index("ix_join_attempts_client_time", "client_hash", "attempted_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_hash = Column(String(64), nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
