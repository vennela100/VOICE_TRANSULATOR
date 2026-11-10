"""Finalized-audio pipeline with persistent verification and idempotent delivery."""
import base64
import logging
from datetime import datetime

from app.models.message import Message
from app.meaning.verifier import verify_translations

logger = logging.getLogger(__name__)
MAX_TRANSCRIPT_CHARS = 4000
MAX_TTS_AUDIO_BYTES = 12 * 1024 * 1024


class MessagePipeline:
    def __init__(self, stt, tts, translation, ws_manager):
        self.stt, self.tts, self.translation, self.ws = stt, tts, translation, ws_manager

    def event(self, kind, message, **data):
        return {"type": kind, "message_id": message.id, "room_id": message.room_id,
                "sender_id": message.sender_id, "timestamp": datetime.utcnow().isoformat(), **data}

    async def process_audio(self, message_id, room_id, sender_id, sender_language,
                            target_language, audio_bytes, db_session):
        row = db_session.query(Message).filter(Message.id == message_id).first()
        if row and row.status in ("awaiting_confirmation", "delivered", "rejected"):
            return
        if not row:
            row = Message(id=message_id, room_id=room_id, sender_id=sender_id,
                          original_language=sender_language, translated_language=target_language,
                          status="processing")
            db_session.add(row)
            db_session.commit()
        try:
            stt_result = await self._retry(lambda: self.stt.transcribe(audio_bytes, sender_language))
            if stt_result.error or stt_result.is_empty or not stt_result.text.strip():
                raise RuntimeError(stt_result.error or "No clear speech was recognized. Try again.")
            row.original_text = stt_result.text.strip()
            if len(row.original_text) > MAX_TRANSCRIPT_CHARS:
                raise RuntimeError("Recognized speech exceeded the supported message length.")
            row.status = "transcribed"
            db_session.commit()
            await self.ws.send_to_all_in_room(room_id, self.event(
                "transcript.final", row, text=row.original_text, language=sender_language))

            translated = await self._retry(lambda: self.translation.translate(
                row.original_text, sender_language, target_language))
            if translated.error or not translated.translated_text.strip():
                raise RuntimeError(translated.error or "Translation returned no text.")
            row.translated_text = translated.translated_text.strip()
            speech_text = (translated.speech_text or row.translated_text).strip()
            if len(row.translated_text) > MAX_TRANSCRIPT_CHARS or len(speech_text) > MAX_TRANSCRIPT_CHARS:
                raise RuntimeError("Translation exceeded the supported message length.")
            row.status = "translated"
            primary = verify_translations(row.original_text, row.translated_text)
            if speech_text != row.translated_text:
                speech_check = verify_translations(row.original_text, speech_text)
                if speech_check["status"] != "ok":
                    primary = speech_check
            low_quality_stt = stt_result.confidence is not None and stt_result.confidence < 0.55
            if low_quality_stt and primary["status"] == "ok":
                primary["status"] = "needs_confirmation"
                primary["prompt_to_speaker"] = (
                    f"I heard: ‘{row.original_text}’. Is this correct? Confirm to deliver, or re-record."
                )
                primary["mismatches"].append({"kind": "transcript", "reason": "low_stt_confidence",
                                               "confidence": stt_result.confidence})
            row.confirmed_entities = {
                "verification": primary,
                "speech_text": speech_text,
                "confirmed": False,
                "meaning_status": "supported_checks_passed" if primary["status"] == "ok" else "confirmation_required",
            }
            db_session.commit()
            await self.ws.send_to_all_in_room(room_id, self.event(
                "translation.completed", row, text=row.translated_text,
                target_language=target_language, verification=primary))
            if primary["status"] != "ok":
                row.needs_confirmation = True
                row.status = "awaiting_confirmation"
                db_session.commit()
                await self.ws.send_to_participant(room_id, sender_id, self.event(
                    "verification.required", row, prompt_text=primary["prompt_to_speaker"],
                    verification=primary))
                await self.ws.broadcast_to_room(room_id, self.event(
                    "verification.pending", row, status="awaiting_confirmation"), exclude=sender_id)
                return
            await self.deliver(row, speech_text, target_language, db_session)
        except Exception as exc:
            logger.warning("Message processing failed (%s, %s)", message_id, type(exc).__name__)
            row.status = "failed"
            db_session.commit()
            await self.ws.send_to_participant(room_id, sender_id, self.event(
                "message.failed", row,
                error="We couldn't process this recording. Please retry or re-record.", retryable=True))

    async def confirm(self, row, db_session):
        if row.status != "awaiting_confirmation":
            return False
        details = dict(row.confirmed_entities or {})
        details["confirmed"] = True
        details["confirmed_at"] = datetime.utcnow().isoformat()
        row.confirmed_entities = details
        row.needs_confirmation = False
        row.status = "verification_confirmed"
        db_session.commit()
        await self.ws.send_to_all_in_room(row.room_id, self.event("verification.confirmed", row))
        await self.deliver(row, details.get("speech_text", row.translated_text),
                           row.translated_language, db_session)
        return True

    async def reject(self, row, db_session):
        if row.status != "awaiting_confirmation":
            return False
        row.status = "rejected"
        db_session.commit()
        await self.ws.send_to_all_in_room(row.room_id, self.event("verification.rejected", row,
                                                                  prompt_text="Please re-record the message."))
        return True

    async def deliver(self, row, speech_text, target_language, db_session):
        if row.status == "delivered":
            return
        audio_error = None
        if row.tts_audio_base64:
            audio_b64 = row.tts_audio_base64
            audio_format = row.tts_audio_format or "wav"
        else:
            try:
                result = await self._retry(lambda: self.tts.synthesize(speech_text, target_language))
                if result.error:
                    raise RuntimeError(result.error)
                if not result.audio_bytes or len(result.audio_bytes) > MAX_TTS_AUDIO_BYTES:
                    raise RuntimeError("Synthesized audio exceeded the supported size limit.")
                audio_b64 = base64.b64encode(result.audio_bytes).decode("ascii")
                audio_format = result.audio_format
                row.tts_audio_base64 = audio_b64
                row.tts_audio_format = audio_format
            except Exception as exc:
                logger.warning("TTS unavailable (%s, %s)", row.id, type(exc).__name__)
                audio_b64, audio_format = None, None
                audio_error = "Translated text is ready, but speech audio is temporarily unavailable."
        row.status = "delivered"
        db_session.commit()
        if audio_b64:
            await self.ws.send_to_all_in_room(row.room_id, self.event(
                "audio.ready", row, audio_base64=audio_b64, audio_format=audio_format))
        await self.ws.send_to_all_in_room(row.room_id, self.event(
            "message.delivered", row, text=row.translated_text,
            audio_available=bool(audio_b64), audio_error=audio_error))

    @staticmethod
    async def _retry(call):
        last = None
        for _ in range(2):
            try:
                result = await call()
                if getattr(result, "error", None):
                    last = RuntimeError(result.error)
                    continue
                return result
            except Exception as exc:
                last = exc
        raise last or RuntimeError("Provider request failed")
