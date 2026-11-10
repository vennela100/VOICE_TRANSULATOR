import base64
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import outcome, message, participant, room  # noqa: F401
from app.pipeline import MessagePipeline
from app.services.stt.provider import SttResult
from app.services.translation.provider import TranslationResult
from app.services.tts.provider import TtsResult
from app import main


class DemoStt:
    async def transcribe(self, audio, language): return SttResult("sava lakh rupaye", language)

class DemoTranslation:
    async def translate(self, text, source, target):
        return TranslationResult("Rs 1,25,000", source, target, speech_text="Rs 1,25,000")

class DemoTts:
    async def synthesize(self, text, language): return TtsResult(b"wav-demo")


def test_two_participant_confirmation_delivery_and_delete(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(main, "SessionLocal", factory)
    monkeypatch.setattr(main, "init_db", lambda: Base.metadata.create_all(engine))
    monkeypatch.setattr(main, "pipeline", MessagePipeline(DemoStt(), DemoTts(), DemoTranslation(), main.manager))
    with TestClient(main.app) as client:
        a = client.post("/api/rooms", json={"participant_name": "A", "language": "hi"}).json()
        b = client.post(f"/api/rooms/{a['room_code']}/join", json={"participant_name": "B", "language": "te"}).json()
        with client.websocket_connect(f"/ws/{a['room_id']}/{a['participant_id']}") as wa:
            wa.send_json({"type": "auth", "token": a["participant_token"]})
            assert wa.receive_json()["type"] == "room.state"
            with client.websocket_connect(f"/ws/{b['room_id']}/{b['participant_id']}") as wb:
                wb.send_json({"type": "auth", "token": b["participant_token"]})
                assert wb.receive_json()["type"] == "room.state"
                assert wa.receive_json()["type"] == "participant_joined"
                message_id = str(uuid.uuid4())
                wa.send_json({"type": "audio_data", "message_id": message_id,
                              "audio_base64": base64.b64encode(b"finalized audio").decode()})
                for expected in ("audio.started", "transcript.final", "translation.completed"):
                    assert wa.receive_json()["type"] == expected
                required = wa.receive_json()
                assert required["type"] == "verification.required"
                assert "1,25,000" in required["prompt_text"]
                # The listener sees transcript and translation, but cannot approve for the speaker.
                assert [wb.receive_json()["type"] for _ in range(3)] == [
                    "audio.started", "transcript.final", "translation.completed"]
                assert wb.receive_json()["type"] == "verification.pending"
                wa.send_json({"type": "verification.confirmed", "message_id": message_id})
                assert wa.receive_json()["type"] == "verification.confirmed"
                assert wa.receive_json()["type"] == "audio.ready"
                assert wa.receive_json()["type"] == "message.delivered"
                assert wb.receive_json()["type"] == "verification.confirmed"
                assert wb.receive_json()["type"] == "audio.ready"
                assert wb.receive_json()["type"] == "message.delivered"
        auth_a = {"Authorization": f"Bearer {a['participant_token']}"}
        draft = client.get(f"/api/rooms/{a['room_code']}/outcome", headers=auth_a).json()
        assert draft["items"][0]["value"] == "Rs 1,25,000"
        assert draft["items"][0]["status"] == "Confirmed"
        assert client.put(f"/api/rooms/{a['room_code']}/outcome", json=draft, headers=auth_a).json()["saved"] is True
        with client.websocket_connect(f"/ws/{a['room_id']}/{a['participant_id']}") as resumed:
            resumed.send_json({"type": "auth", "token": a["participant_token"]})
            state = resumed.receive_json()
            assert state["type"] == "room.state"
            assert state["messages"][-1]["status"] == "delivered"
            assert state["messages"][-1]["audio_base64"]
        assert client.delete(f"/api/rooms/{a['room_code']}", headers=auth_a).json() == {"deleted": True}
        assert client.get(f"/api/rooms/{a['room_code']}").status_code == 404
