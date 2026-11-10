import base64
import asyncio
import binascii
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.auth import create_room_token, require_room_token, verify_room_token
from app.security import JoinAttemptLimiter
from app.db.session import init_db, SessionLocal
from app.models.room import Room, generate_room_code
from app.models.participant import Participant
from app.models.message import Message
from app.models.outcome import Outcome
from app.models import outcome as _outcome_model  # ensure table registration
from app.ws.manager import manager
from app.pipeline import MessagePipeline
from app.services.stt.mock import MockSttProvider
from app.services.stt.gnani import GnaniPrismaProvider
from app.services.tts.mock import MockTtsProvider
from app.services.tts.gnani import GnaniTimbreProvider
from app.services.tts.gemini import GeminiTtsProvider
from app.services.tts.fallback import FallbackTtsProvider
from app.services.translation.mock import MockTranslationProvider
from app.services.translation.gemini_translate import GeminiTranslationProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try: _clean_expired(db)
    finally: db.close()
    async def expire_rooms():
        while True:
            await asyncio.sleep(60)
            session = SessionLocal()
            try: _clean_expired(session)
            finally: session.close()
    expiry_task = asyncio.create_task(expire_rooms())
    try: yield
    finally:
        expiry_task.cancel()
        try: await expiry_task
        except asyncio.CancelledError: pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)
cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

stt_provider = (GnaniPrismaProvider(api_key_id=settings.gnani_api_key_id, endpoint=settings.prisma_endpoint)
                if settings.stt_provider == "gnani" else MockSttProvider())
if settings.tts_provider == "gnani":
    primary_tts = GnaniTimbreProvider(api_key_id=settings.gnani_api_key_id, endpoint=settings.timbre_endpoint,
                                      hindi_voice=settings.timbre_hindi_voice, telugu_voice=settings.timbre_telugu_voice)
    tts_provider = (FallbackTtsProvider(primary_tts, GeminiTtsProvider(settings.gemini_api_key, settings.gemini_tts_model))
                    if settings.gemini_api_key else primary_tts)
elif settings.tts_provider == "gemini":
    tts_provider = GeminiTtsProvider(settings.gemini_api_key, settings.gemini_tts_model)
else:
    tts_provider = MockTtsProvider()
translation_provider = (GeminiTranslationProvider(api_key=settings.gemini_api_key, model=settings.gemini_model,
                                                  fallback_model=settings.gemini_fallback_model)
                        if settings.translation_provider == "gemini" else MockTranslationProvider())
if settings.stt_provider not in {"mock", "gnani"} or settings.tts_provider not in {"mock", "gnani", "gemini"} or settings.translation_provider not in {"mock", "gemini"}:
    raise ValueError("Provider environment setting is invalid")
pipeline = MessagePipeline(stt_provider, tts_provider, translation_provider, manager)
participant_languages: dict[str, dict[str, str]] = {}
join_attempt_limiter = JoinAttemptLimiter()
MAX_INPUT_AUDIO_BYTES = 12 * 1024 * 1024
ROOM_CODE_GENERATION_ATTEMPTS = 5


SUPPORTED_LANGUAGES = {
    "hi", "en", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "or", "ur"
}


class ParticipantRequest(BaseModel):
    participant_name: str = Field(min_length=1, max_length=60)
    language: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, value):
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}")
        return value

class OutcomeSave(BaseModel):
    items: list[dict] = Field(default_factory=list)
    decisions: list[dict] = Field(default_factory=list)
    next_steps: list[dict] = Field(default_factory=list)


def _clean_expired(db):
    now = datetime.utcnow()
    expired_ids = [row.id for row in db.query(Room.id).filter(Room.expires_at <= now).all()]
    if expired_ids:
        db.query(Message).filter(Message.room_id.in_(expired_ids)).delete(synchronize_session=False)
        db.query(Outcome).filter(Outcome.room_id.in_(expired_ids)).delete(synchronize_session=False)
        db.query(Participant).filter(Participant.room_id.in_(expired_ids)).delete(synchronize_session=False)
        db.query(Room).filter(Room.id.in_(expired_ids)).delete(synchronize_session=False)
        for room_id in expired_ids:
            participant_languages.pop(room_id, None)
    db.commit()


def _room_history(db, room_id):
    rows = db.query(Message).filter(Message.room_id == room_id).order_by(Message.created_at.desc()).limit(50).all()
    return [{"message_id": m.id, "room_id": m.room_id, "sender_id": m.sender_id,
             "original_text": m.original_text, "original_language": m.original_language,
             "translated_text": m.translated_text, "translated_language": m.translated_language,
             "status": m.status, "needs_confirmation": m.needs_confirmation,
             "verification": (m.confirmed_entities or {}).get("verification"),
             "confirmed": (m.confirmed_entities or {}).get("confirmed", False),
             "audio_base64": m.tts_audio_base64, "audio_format": m.tts_audio_format or "wav",
             "timestamp": m.created_at.isoformat() if m.created_at else None}
            for m in reversed(rows)]


@app.get("/api/status")
def get_status():
    return {"stt_provider": settings.stt_provider, "translation_provider": settings.translation_provider,
            "tts_provider": settings.tts_provider,
            "stt_configured": settings.stt_provider == "mock" or bool(settings.gnani_api_key_id),
            "tts_configured": (settings.tts_provider == "mock" or
                               (settings.tts_provider == "gnani" and
                                (bool(settings.gnani_api_key_id) or bool(settings.gemini_api_key))) or
                               (settings.tts_provider == "gemini" and bool(settings.gemini_api_key))),
            "tts_fallback_provider": "gemini" if settings.tts_provider == "gnani" and settings.gemini_api_key else None,
            "translation_configured": settings.translation_provider == "mock" or bool(settings.gemini_api_key)}


@app.post("/api/rooms")
def create_room(req: ParticipantRequest):
    db = SessionLocal()
    try:
        _clean_expired(db)
        room = None
        for _ in range(ROOM_CODE_GENERATION_ATTEMPTS):
            candidate = Room(code=generate_room_code(), expires_at=datetime.utcnow() +
                             timedelta(minutes=settings.room_expiry_minutes))
            db.add(candidate)
            try:
                db.flush()
                room = candidate
                break
            except IntegrityError:
                db.rollback()
        if room is None:
            raise HTTPException(503, "Could not allocate a room code. Please try again.")
        participant = Participant(room_id=room.id, name=req.participant_name, language=req.language)
        db.add(participant); db.commit()
        participant_languages[room.id] = {participant.id: participant.language}
        return {"room_id": room.id, "room_code": room.code, "participant_id": participant.id,
                "participant_token": create_room_token(room.id, participant.id, room.expires_at,
                                                        can_delete_room=True)}
    finally:
        db.close()


@app.post("/api/rooms/{room_code}/join")
def join_room(room_code: str, req: ParticipantRequest, request: Request):
    client_key = request.client.host if request.client else "unknown"
    db = SessionLocal()
    try:
        join_attempt_limiter.reserve(client_key, db)
        _clean_expired(db)
        room = db.query(Room).filter(Room.code == room_code.upper(), Room.is_active.is_(True)).first()
        if not room:
            raise HTTPException(404, "Room not found or expired")
        participants = db.query(Participant).filter(Participant.room_id == room.id).all()
        if len(participants) >= 2:
            raise HTTPException(400, "Room is full (max 2 participants)")
        participant = Participant(room_id=room.id, name=req.participant_name, language=req.language)
        db.add(participant); db.commit(); db.refresh(participant)
        join_attempt_limiter.clear(client_key, db)
        participant_languages.setdefault(room.id, {})[participant.id] = participant.language
        participants = db.query(Participant).filter(Participant.room_id == room.id).all()
        return {"room_id": room.id, "room_code": room.code, "participant_id": participant.id,
                "participant_token": create_room_token(room.id, participant.id, room.expires_at),
                "participants": [{"id": p.id, "name": p.name, "language": p.language} for p in participants]}
    finally:
        db.close()


@app.get("/api/rooms/{room_code}")
def get_room(room_code: str, authorization: str | None = Header(default=None)):
    db = SessionLocal()
    try:
        _clean_expired(db)
        room = db.query(Room).filter(Room.code == room_code.upper(), Room.is_active.is_(True)).first()
        if not room: raise HTTPException(404, "Room not found or expired")
        require_room_token(authorization, room.id)
        participants = db.query(Participant).filter(Participant.room_id == room.id).all()
        return {"room_id": room.id, "room_code": room.code, "is_active": room.is_active,
                "participants": [{"id": p.id, "name": p.name, "language": p.language} for p in participants]}
    finally: db.close()


@app.get("/api/rooms/{room_code}/outcome")
async def get_outcome(room_code: str, authorization: str | None = Header(default=None)):
    from app.services.outcome import add_ai_summary, build_outcome
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code.upper(), Room.is_active.is_(True)).first()
        if not room: raise HTTPException(404, "Room not found")
        require_room_token(authorization, room.id)
        saved = db.query(Outcome).filter(Outcome.room_id == room.id).first()
        return saved.payload if saved else await add_ai_summary(db, room.id, build_outcome(db, room.id), settings)
    finally: db.close()


@app.put("/api/rooms/{room_code}/outcome")
def save_outcome(room_code: str, req: OutcomeSave, authorization: str | None = Header(default=None)):
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code.upper(), Room.is_active.is_(True)).first()
        if not room: raise HTTPException(404, "Room not found")
        require_room_token(authorization, room.id)
        payload = req.model_dump()
        entry = db.query(Outcome).filter(Outcome.room_id == room.id).first()
        if entry: entry.payload = payload
        else: db.add(Outcome(room_id=room.id, payload=payload))
        db.commit()
        return {"saved": True, **payload}
    finally: db.close()


@app.delete("/api/rooms/{room_code}")
async def delete_session(room_code: str, authorization: str | None = Header(default=None)):
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code.upper()).first()
        if not room: raise HTTPException(404, "Room not found")
        require_room_token(authorization, room.id, require_delete_permission=True)
        await manager.send_to_all_in_room(room.id, {"type": "session.deleted", "room_id": room.id,
            "sender_id": "", "timestamp": datetime.utcnow().isoformat()})
        for socket in list(manager.rooms.get(room.id, {}).values()):
            try: await socket.close(code=4001)
            except Exception: pass
        manager.rooms.pop(room.id, None)
        db.query(Message).filter(Message.room_id == room.id).delete(synchronize_session=False)
        db.query(Outcome).filter(Outcome.room_id == room.id).delete(synchronize_session=False)
        db.query(Participant).filter(Participant.room_id == room.id).delete(synchronize_session=False)
        db.delete(room); db.commit()
        participant_languages.pop(room.id, None)
        return {"deleted": True}
    finally: db.close()


@app.websocket("/ws/{room_id}/{participant_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, participant_id: str):
    db = SessionLocal()
    try:
        participant = db.query(Participant).filter(Participant.id == participant_id, Participant.room_id == room_id).first()
        room = db.query(Room).filter(Room.id == room_id, Room.is_active.is_(True), Room.expires_at > datetime.utcnow()).first()
        if not participant or not room:
            await websocket.accept(); await websocket.close(code=4404); return
        await websocket.accept()
        try:
            auth_message = await asyncio.wait_for(websocket.receive_text(), timeout=5)
            auth_payload = json.loads(auth_message)
        except (asyncio.TimeoutError, json.JSONDecodeError, WebSocketDisconnect):
            await websocket.close(code=4401)
            return
        if (not isinstance(auth_payload, dict) or auth_payload.get("type") != "auth"
                or not verify_room_token(auth_payload.get("token", ""), room_id, participant_id)):
            await websocket.close(code=4401)
            return
        participant_languages.setdefault(room_id, {})[participant_id] = participant.language
        participants = db.query(Participant).filter(Participant.room_id == room_id).all()
        manager.rooms.setdefault(room_id, {})[participant_id] = websocket
        await manager.send_to_participant(room_id, participant_id, {
            "type": "room.state", "room_id": room_id, "sender_id": participant_id,
            "timestamp": datetime.utcnow().isoformat(), "participants": [
                {"id": p.id, "name": p.name, "language": p.language} for p in participants],
            "messages": _room_history(db, room_id)})
        await manager.broadcast_to_room(room_id, {"type": "participant_joined", "room_id": room_id,
             "sender_id": participant_id, "participant_id": participant_id, "name": participant.name,
             "language": participant.language, "timestamp": datetime.utcnow().isoformat()}, exclude=participant_id)
    finally: db.close()
    try:
        while True:
            incoming = await websocket.receive_text()
            try: payload = json.loads(incoming)
            except json.JSONDecodeError:
                await manager.send_to_participant(room_id, participant_id, {"type": "error", "error": "Invalid JSON"}); continue
            kind = payload.get("type")
            if kind == "ping":
                await manager.send_to_participant(room_id, participant_id, {"type": "pong", "room_id": room_id,
                    "sender_id": participant_id, "timestamp": datetime.utcnow().isoformat()}); continue
            if kind in {"verification.confirmed", "verification.rejected"}:
                db = SessionLocal()
                try:
                    row = db.query(Message).filter(Message.id == payload.get("message_id"), Message.room_id == room_id,
                                                   Message.sender_id == participant_id).first()
                    if not row: continue
                    if kind.endswith("confirmed"): await pipeline.confirm(row, db)
                    else: await pipeline.reject(row, db)
                finally: db.close()
                continue
            if kind != "audio_data": continue
            message_id = payload.get("message_id")
            try: message_id = str(uuid.UUID(message_id))
            except (ValueError, TypeError, AttributeError):
                await manager.send_to_participant(room_id, participant_id, {"type": "message.failed",
                    "message_id": str(message_id or uuid.uuid4()), "room_id": room_id, "sender_id": participant_id,
                    "error": "Invalid message ID", "retryable": False, "timestamp": datetime.utcnow().isoformat()}); continue
            encoded_audio = payload.get("audio_base64", "")
            max_encoded_audio_chars = ((MAX_INPUT_AUDIO_BYTES + 2) // 3) * 4
            if not isinstance(encoded_audio, str) or len(encoded_audio) > max_encoded_audio_chars:
                audio = b""
            else:
                try: audio = base64.b64decode(encoded_audio, validate=True)
                except (binascii.Error, ValueError): audio = b""
            if not audio or len(audio) > MAX_INPUT_AUDIO_BYTES:
                await manager.send_to_participant(room_id, participant_id, {"type": "message.failed",
                    "message_id": message_id, "room_id": room_id, "sender_id": participant_id,
                    "error": "Audio was empty or too large (maximum 12 MB). Please record again.",
                    "retryable": True, "timestamp": datetime.utcnow().isoformat()}); continue
            db = SessionLocal()
            try:
                _clean_expired(db)
                active = db.query(Room).filter(Room.id == room_id, Room.is_active.is_(True),
                                               Room.expires_at > datetime.utcnow()).first()
                if not active:
                    await websocket.close(code=4404)
                    manager.disconnect(room_id, participant_id)
                    return
                duplicate = db.query(Message).filter(Message.id == message_id).first()
                if duplicate:
                    if duplicate.status == "failed":
                        db.delete(duplicate); db.commit()
                    else: continue
                sender = db.query(Participant).filter(Participant.id == participant_id).first()
                members = db.query(Participant).filter(Participant.room_id == room_id).all()
                receiver = next((p for p in members if p.id != participant_id), None)
                sender_lang = sender.language
                target_lang = receiver.language if receiver else ("en" if sender_lang != "en" else "hi")
                event = {"type": "audio.started", "message_id": message_id, "room_id": room_id,
                         "sender_id": participant_id, "timestamp": datetime.utcnow().isoformat()}
                await manager.send_to_all_in_room(room_id, event)
                await pipeline.process_audio(message_id, room_id, participant_id, sender_lang,
                                             target_lang, audio, db)
            finally: db.close()
    except WebSocketDisconnect:
        manager.disconnect(room_id, participant_id)
        await manager.broadcast_to_room(room_id, {"type": "participant_left", "room_id": room_id,
            "sender_id": participant_id, "participant_id": participant_id, "timestamp": datetime.utcnow().isoformat()})
    except Exception:
        logger.exception("WebSocket handler failed")
        manager.disconnect(room_id, participant_id)
