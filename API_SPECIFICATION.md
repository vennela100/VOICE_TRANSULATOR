# API and WebSocket Contract (MVP)

HTTP JSON routes are served by FastAPI. Provider credentials are never accepted from the browser.

| Method and route | Purpose |
|---|---|
| `GET /api/status` | Reports configured provider names and key-presence flags; not a live health check. |
| `POST /api/rooms` | Create a room and first participant (`participant_name`, `language: hi|en|te|ta|kn|ml|mr|bn|gu|pa|or|ur`). |
| `POST /api/rooms/{room_code}/join` | Join an available room using the six-character code. |
| `GET /api/rooms/{room_code}` | Read room participant summary with that participant's bearer capability. |
| `GET /api/rooms/{room_code}/outcome` | Build or retrieve the conversation Outcome Card with participant authorization. |
| `PUT /api/rooms/{room_code}/outcome` | Save edited card fields with participant authorization. |
| `DELETE /api/rooms/{room_code}` | Delete room, participants, messages and outcome; creator capability required. |
| `WS /ws/{room_id}/{participant_id}` | Room state and conversation events. |

## WebSocket events

After connecting, the client must send `{ "type": "auth", "token": "<participant capability>" }` within five seconds. It then sends `audio_data` (`message_id`, base64 audio; maximum decoded size 12 MiB), `verification.confirmed`, `verification.rejected`, and `ping`. Server sends `room.state`, `participant_joined`, `participant_left`, `audio.started`, `transcript.final`, `translation.completed`, `verification.required`, `verification.pending`, `verification.confirmed`, `verification.rejected`, `audio.ready`, `message.delivered`, `message.failed`, `error`, and `pong`. `translation.completed` includes a `verification` object with the supported-check result, `checks_scope`, and `overall_meaning_verified: false`; it never certifies complete sentence meaning. Extracted spoken numeric entities include `mapping_status` (`inferred`, `provisional`, or `ambiguous`); digit-only parses are `literal`. `audio.ready` includes `audio_format`; message history preserves that format and defaults older rows to WAV. Transcript/translation and synthesized speech text are limited to 4,000 characters; generated audio is limited to 12 MiB.

## Contract caveats

- This is an implementation inventory, not a versioned public API guarantee.
- Audio event payloads include base64, increasing message size and memory use; clients should discard audio data after playback when possible.
- Room routes use signed participant capabilities and the WebSocket must authenticate before receiving room broadcasts. These controls have automated coverage but have not received a formal penetration test.
- Room joins reserve one of 10 attempts per 10-minute window in SQLite before code lookup. The address is SHA-256 hashed in storage; workers share the counter only when they share the same SQLite database. The deployment proxy must be configured so the backend's client address is trustworthy.
- Room creation retries a unique-code collision up to five times before returning a retryable service error.
- `/api/status` indicates configuration presence only and does not make provider calls.
