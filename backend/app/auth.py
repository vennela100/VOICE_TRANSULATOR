"""Signed, short-lived participant capability tokens for room access."""
import base64
import hashlib
import hmac
import json
import time
from datetime import timezone

from fastapi import HTTPException

from app.config import get_room_token_secret


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_room_token(room_id: str, participant_id: str, expires_at, *, can_delete_room: bool = False) -> str:
    payload = _b64encode(json.dumps({
        "room_id": room_id,
        "participant_id": participant_id,
        "can_delete_room": can_delete_room,
        "exp": int(expires_at.replace(tzinfo=timezone.utc).timestamp()),
    }, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(get_room_token_secret(), payload.encode("ascii"), hashlib.sha256).digest()
    return f"{payload}.{_b64encode(signature)}"


def verify_room_token(token: str, room_id: str, participant_id: str) -> bool:
    try:
        payload_part, signature_part = token.split(".", 1)
        expected = hmac.new(get_room_token_secret(), payload_part.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature_part)):
            return False
        payload = json.loads(_b64decode(payload_part))
        return (payload.get("room_id") == room_id
                and payload.get("participant_id") == participant_id
                and isinstance(payload.get("exp"), int)
                and payload["exp"] > int(time.time()))
    except (ValueError, TypeError, AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def require_room_token(
    authorization: str | None,
    room_id: str,
    participant_id: str | None = None,
    *,
    require_delete_permission: bool = False,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Participant authorization required")
    token = authorization[7:]
    try:
        payload_part = token.split(".", 1)[0]
        payload = json.loads(_b64decode(payload_part))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid participant authorization")
    token_participant_id = payload.get("participant_id") if isinstance(payload, dict) else None
    expected_participant_id = participant_id or token_participant_id
    if not expected_participant_id or not verify_room_token(token, room_id, expected_participant_id):
        raise HTTPException(status_code=401, detail="Invalid or expired participant authorization")
    if require_delete_permission and not payload.get("can_delete_room", False):
        raise HTTPException(status_code=403, detail="Only the room creator can end the session")
    return expected_participant_id
