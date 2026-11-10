from fastapi import WebSocket
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections organized by room."""

    def __init__(self):
        # room_id -> {participant_id -> WebSocket}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, participant_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][participant_id] = websocket
        logger.info(f"Participant {participant_id} connected to room {room_id}")

    def disconnect(self, room_id: str, participant_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].pop(participant_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        logger.info(f"Participant {participant_id} disconnected from room {room_id}")

    async def send_to_participant(self, room_id: str, participant_id: str, data: dict):
        if room_id in self.rooms and participant_id in self.rooms[room_id]:
            ws = self.rooms[room_id][participant_id]
            await ws.send_json(data)

    async def broadcast_to_room(self, room_id: str, data: dict, exclude: str = None):
        """Send to all participants except the excluded one."""
        if room_id in self.rooms:
            for pid, ws in list(self.rooms[room_id].items()):
                if pid != exclude:
                    try:
                        await ws.send_json(data)
                    except Exception as e:
                        logger.error(f"Failed to send to {pid}: {e}")

    async def send_to_all_in_room(self, room_id: str, data: dict):
        """Send to ALL participants including sender."""
        if room_id in self.rooms:
            for pid, ws in list(self.rooms[room_id].items()):
                try:
                    await ws.send_json(data)
                except Exception as e:
                    logger.error(f"Failed to send to {pid}: {e}")

    def get_participants_in_room(self, room_id: str) -> list:
        if room_id in self.rooms:
            return list(self.rooms[room_id].keys())
        return []


manager = ConnectionManager()
