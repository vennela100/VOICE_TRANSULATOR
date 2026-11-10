"""SQLite-backed join throttling shared by workers using the same database."""

import hashlib
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.join_attempt import JoinAttempt


class JoinAttemptLimiter:
    def __init__(self, limit: int = 10, window_seconds: int = 600):
        self.limit = limit
        self.window_seconds = window_seconds

    @staticmethod
    def _client_hash(client_key: str) -> str:
        return hashlib.sha256(client_key.encode("utf-8", errors="replace")).hexdigest()

    def reserve(self, client_key: str, db: Session) -> None:
        """Atomically reserve one join attempt or reject the client.

        The short SQLite IMMEDIATE transaction serializes reservations across
        application workers sharing this database. No room lookup or provider
        call is performed while the write lock is held.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        client_hash = self._client_hash(client_key)
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        try:
            db.query(JoinAttempt).filter(JoinAttempt.attempted_at < cutoff).delete(
                synchronize_session=False
            )
            recent_count = db.query(JoinAttempt).filter(
                JoinAttempt.client_hash == client_hash,
                JoinAttempt.attempted_at >= cutoff,
            ).count()
            if recent_count >= self.limit:
                db.rollback()
                raise HTTPException(
                    status_code=429,
                    detail="Too many room join attempts. Try again later.",
                )
            db.add(JoinAttempt(client_hash=client_hash, attempted_at=now))
            db.commit()
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            raise

    def clear(self, client_key: str, db: Session) -> None:
        client_hash = self._client_hash(client_key)
        db.query(JoinAttempt).filter(JoinAttempt.client_hash == client_hash).delete(
            synchronize_session=False
        )
        db.commit()
