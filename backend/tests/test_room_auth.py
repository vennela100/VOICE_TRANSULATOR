import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.websockets import WebSocketDisconnect

from app import main
from app.db.session import Base
from app.models import outcome, message, participant, room as room_model  # noqa: F401
from app.models.join_attempt import JoinAttempt
from app.security import JoinAttemptLimiter


@pytest.fixture
def room_client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(main, "SessionLocal", factory)
    monkeypatch.setattr(main, "init_db", lambda: Base.metadata.create_all(engine))
    with TestClient(main.app) as client:
        created = client.post("/api/rooms", json={"participant_name": "A", "language": "hi"})
        assert created.status_code == 200
        room = created.json()
        yield client, room
        client.delete(f"/api/rooms/{room['room_code']}",
                      headers={"Authorization": f"Bearer {room['participant_token']}"})


def test_sensitive_room_routes_require_participant_token(room_client):
    client, room = room_client
    code = room["room_code"]
    assert client.get(f"/api/rooms/{code}").status_code == 401
    assert client.get(f"/api/rooms/{code}/outcome").status_code == 401
    assert client.put(f"/api/rooms/{code}/outcome", json={}).status_code == 401
    assert client.delete(f"/api/rooms/{code}").status_code == 401


def test_only_room_creator_can_delete_session(room_client):
    client, room = room_client
    joined = client.post(f"/api/rooms/{room['room_code']}/join",
                         json={"participant_name": "B", "language": "te"}).json()
    headers = {"Authorization": f"Bearer {joined['participant_token']}"}
    assert client.delete(f"/api/rooms/{room['room_code']}", headers=headers).status_code == 403
    owner_headers = {"Authorization": f"Bearer {room['participant_token']}"}
    assert client.delete(f"/api/rooms/{room['room_code']}", headers=owner_headers).status_code == 200


def test_participant_token_is_room_scoped_and_allows_protected_routes(room_client):
    client, room = room_client
    headers = {"Authorization": f"Bearer {room['participant_token']}"}
    assert client.get(f"/api/rooms/{room['room_code']}", headers=headers).status_code == 200
    assert client.get(f"/api/rooms/{room['room_code']}/outcome", headers=headers).status_code == 200
    other = client.post("/api/rooms", json={"participant_name": "B", "language": "te"}).json()
    try:
        assert client.get(f"/api/rooms/{other['room_code']}", headers=headers).status_code == 401
    finally:
        client.delete(f"/api/rooms/{other['room_code']}",
                      headers={"Authorization": f"Bearer {other['participant_token']}"})


def test_join_by_code_remains_public_and_returns_distinct_capability(room_client):
    client, room = room_client
    joined = client.post(f"/api/rooms/{room['room_code']}/join",
                         json={"participant_name": "B", "language": "te"})
    assert joined.status_code == 200
    assert joined.json()["participant_token"] != room["participant_token"]


def test_websocket_requires_participant_token(room_client):
    client, room = room_client
    with client.websocket_connect(f"/ws/{room['room_id']}/{room['participant_id']}") as ws:
        ws.send_json({"type": "auth", "token": "invalid"})
        with pytest.raises(WebSocketDisconnect) as disconnected:
            ws.receive_json()
        assert disconnected.value.code == 4401


def test_websocket_authentication_is_first_message(room_client):
    client, room = room_client
    with client.websocket_connect(f"/ws/{room['room_id']}/{room['participant_id']}") as ws:
        ws.send_json({"type": "ping"})
        with pytest.raises(WebSocketDisconnect) as disconnected:
            ws.receive_json()
        assert disconnected.value.code == 4401


def test_failed_room_code_joins_are_rate_limited(room_client):
    client, _ = room_client
    for _ in range(10):
        assert client.post("/api/rooms/ZZZZZZ/join",
                           json={"participant_name": "Guess", "language": "te"}).status_code == 404
    assert client.post("/api/rooms/ZZZZZZ/join",
                       json={"participant_name": "Guess", "language": "te"}).status_code == 429


def test_join_attempts_are_shared_between_limiter_instances(room_client):
    _, _room = room_client
    db = main.SessionLocal()
    try:
        first_worker = JoinAttemptLimiter(limit=2)
        second_worker = JoinAttemptLimiter(limit=2)
        first_worker.reserve("192.0.2.10", db)
        first_worker.reserve("192.0.2.10", db)
        with pytest.raises(HTTPException) as blocked:
            second_worker.reserve("192.0.2.10", db)
        assert blocked.value.status_code == 429
        hashes = [row.client_hash for row in db.query(JoinAttempt).all()]
        assert hashes and "192.0.2.10" not in hashes
    finally:
        db.close()


def test_room_code_collision_retries_before_giving_up(room_client, monkeypatch):
    client, existing = room_client
    codes = iter((existing["room_code"], "Q7M4XZ"))
    monkeypatch.setattr(main, "generate_room_code", lambda: next(codes))
    response = client.post("/api/rooms", json={"participant_name": "Retry", "language": "hi"})
    assert response.status_code == 200
    created = response.json()
    assert created["room_code"] == "Q7M4XZ"
    client.delete(f"/api/rooms/{created['room_code']}",
                  headers={"Authorization": f"Bearer {created['participant_token']}"})


def test_concurrent_join_reservations_do_not_exceed_shared_limit(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'join-limit.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    first_worker = JoinAttemptLimiter(limit=10)
    second_worker = JoinAttemptLimiter(limit=10)
    with factory() as db:
        for _ in range(9):
            first_worker.reserve("192.0.2.11", db)

    start_together = Barrier(2)

    def reserve(limiter):
        with factory() as db:
            start_together.wait()
            try:
                limiter.reserve("192.0.2.11", db)
                return "allowed"
            except HTTPException as exc:
                return exc.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, (first_worker, second_worker)))
        assert sorted(results, key=str) == [429, "allowed"]
        with factory() as db:
            assert db.query(JoinAttempt).count() == 10
    finally:
        engine.dispose()
