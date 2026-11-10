# Database Schema

The initial implementation uses SQLAlchemy with SQLite and creates tables at application startup.

| Table | Stored fields and purpose |
|---|---|
| `rooms` | Room UUID, unique six-character code, creation/expiry times, active flag. |
| `participants` | Participant UUID, room foreign key, display name, language, join time, connected flag. |
| `messages` | Sender/room IDs, original and translated text/languages, status, confirmation JSON, synthesized audio as base64 with its format, creation time. |
| `outcomes` | Room ID and editable JSON Outcome Card payload. |
| `join_attempts` | Hashed client address and timestamp for shared room-join throttling; stale rows are pruned during joins. |

Input audio is not stored in this schema. Generated audio and transcript content are sensitive conversation data; deletion and expiry cleanup remove associated rows. Startup applies one additive SQLite compatibility migration for `messages.tts_audio_format`. `create_all` and this small migration do not provide a general migration strategy, so production schema evolution still requires migration tooling.
