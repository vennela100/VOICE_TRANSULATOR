import asyncio
import base64

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.message import Message
from app.models import room, participant  # noqa: F401 - register metadata
from app.pipeline import MessagePipeline
from app.services.stt.provider import SttResult
from app.services.translation.provider import TranslationResult
from app.services.tts.provider import TtsResult


class FakeStt:
    async def transcribe(self, audio, language):
        return SttResult("sava lakh rupaye", language)


class FailingStt:
    async def transcribe(self, audio, language):
        raise RuntimeError("provider response contains private diagnostic details")


class FakeTranslation:
    async def translate(self, text, source, target):
        return TranslationResult("Rs 1,25,000", source, target, speech_text="Rs 1,25,000")


class StatementStt:
    async def transcribe(self, audio, language):
        return SttResult("Do not send the 5 kg package", language)


class ChangedStatementTranslation:
    async def translate(self, text, source, target):
        return TranslationResult("Send the 10 kilograms package", source, target)


class LongTranslation:
    async def translate(self, text, source, target):
        return TranslationResult("x" * 4001, source, target)


class PlainStt:
    async def transcribe(self, audio, language):
        return SttResult("hello there", language)


class PlainTranslation:
    async def translate(self, text, source, target):
        return TranslationResult("namaste", source, target)


class OversizedTts:
    async def synthesize(self, text, language):
        return TtsResult(b"x" * (12 * 1024 * 1024 + 1), "wav")


class FakeTts:
    def __init__(self, audio_format="wav"):
        self.calls = 0
        self.audio_format = audio_format
    async def synthesize(self, text, language):
        self.calls += 1
        return TtsResult(b"demo-audio", self.audio_format)


class FakeWs:
    def __init__(self): self.all = []; self.private = []
    async def send_to_all_in_room(self, room_id, data): self.all.append(data)
    async def send_to_participant(self, room_id, participant_id, data): self.private.append((participant_id, data))
    async def broadcast_to_room(self, room_id, data, exclude=None): self.all.append(data)


def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_fractional_amount_waits_for_speaker_then_synthesizes_once():
    db = session_factory(); tts = FakeTts(); ws = FakeWs()
    pipeline = MessagePipeline(FakeStt(), tts, FakeTranslation(), ws)
    asyncio.run(pipeline.process_audio("m-1", "room", "speaker", "hi", "te", b"audio", db))
    row = db.query(Message).filter_by(id="m-1").one()
    assert row.status == "awaiting_confirmation"
    assert tts.calls == 0
    assert ws.private[0][0] == "speaker"
    assert ws.private[0][1]["type"] == "verification.required"
    asyncio.run(pipeline.confirm(row, db))
    assert row.status == "delivered"
    assert tts.calls == 1
    assert base64.b64decode(row.tts_audio_base64) == b"demo-audio"
    assert row.tts_audio_format == "wav"
    asyncio.run(pipeline.confirm(row, db))
    assert tts.calls == 1


def test_audio_format_is_persisted_and_reused_for_cached_audio():
    db = session_factory(); tts = FakeTts(audio_format="mp3"); ws = FakeWs()
    pipeline = MessagePipeline(FakeStt(), tts, FakeTranslation(), ws)
    row = Message(id="m-mp3", room_id="room", sender_id="speaker",
                  translated_text="Hello", translated_language="te", status="translated")
    db.add(row); db.commit()

    asyncio.run(pipeline.deliver(row, "Hello", "te", db))
    assert row.tts_audio_format == "mp3"
    assert ws.all[-2]["type"] == "audio.ready"
    assert ws.all[-2]["audio_format"] == "mp3"

    row.status = "translated"
    db.commit()
    asyncio.run(pipeline.deliver(row, "Hello", "te", db))
    assert tts.calls == 1
    assert ws.all[-2]["type"] == "audio.ready"
    assert ws.all[-2]["audio_format"] == "mp3"


def test_translation_over_limit_fails_before_synthesis():
    db = session_factory(); tts = FakeTts(); ws = FakeWs()
    pipeline = MessagePipeline(FakeStt(), tts, LongTranslation(), ws)
    asyncio.run(pipeline.process_audio("m-long-translation", "room", "speaker", "hi", "te", b"audio", db))
    row = db.query(Message).filter_by(id="m-long-translation").one()
    assert row.status == "failed"
    assert tts.calls == 0
    assert ws.private[-1][1]["type"] == "message.failed"


def test_oversized_speech_audio_falls_back_to_translated_text():
    db = session_factory(); ws = FakeWs()
    pipeline = MessagePipeline(PlainStt(), OversizedTts(), PlainTranslation(), ws)
    asyncio.run(pipeline.process_audio("m-large-audio", "room", "speaker", "hi", "te", b"audio", db))
    row = db.query(Message).filter_by(id="m-large-audio").one()
    assert row.status == "delivered"
    assert row.tts_audio_base64 is None
    delivered = next(event for event in ws.all if event["type"] == "message.delivered")
    assert delivered["audio_available"] is False
    assert delivered["audio_error"]
    assert row.confirmed_entities["meaning_status"] == "supported_checks_passed"
    assert row.confirmed_entities["verification"]["overall_meaning_verified"] is False
    assert "language_mapping_verified" not in row.confirmed_entities


def test_rejected_amount_is_never_synthesized():
    db = session_factory(); tts = FakeTts(); ws = FakeWs()
    pipeline = MessagePipeline(FakeStt(), tts, FakeTranslation(), ws)
    asyncio.run(pipeline.process_audio("m-2", "room", "speaker", "hi", "te", b"audio", db))
    row = db.query(Message).filter_by(id="m-2").one()
    asyncio.run(pipeline.reject(row, db))
    assert row.status == "rejected"
    assert row.tts_audio_base64 is None
    assert tts.calls == 0


def test_provider_exception_details_are_not_sent_to_clients():
    db = session_factory(); ws = FakeWs()
    pipeline = MessagePipeline(FailingStt(), FakeTts(), FakeTranslation(), ws)
    asyncio.run(pipeline.process_audio("m-safe-error", "room", "speaker", "hi", "te", b"audio", db))
    error_event = ws.private[-1][1]
    assert error_event["type"] == "message.failed"
    assert "private diagnostic details" not in error_event["error"]


def test_measurement_and_negation_mismatches_wait_before_speech_delivery():
    db = session_factory(); tts = FakeTts(); ws = FakeWs()
    pipeline = MessagePipeline(StatementStt(), tts, ChangedStatementTranslation(), ws)
    asyncio.run(pipeline.process_audio("m-meaning-check", "room", "speaker", "hi", "te", b"audio", db))

    row = db.query(Message).filter_by(id="m-meaning-check").one()
    mismatches = row.confirmed_entities["verification"]["mismatches"]
    assert row.status == "awaiting_confirmation"
    assert {item["kind"] for item in mismatches} >= {"measurement", "negation"}
    assert tts.calls == 0

    asyncio.run(pipeline.confirm(row, db))
    assert row.status == "delivered"
    assert tts.calls == 1
