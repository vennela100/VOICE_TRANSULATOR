# Requirements and Acceptance Criteria

## MVP user journey

1. A Hindi speaker creates a room; a Telugu speaker joins by room code, or vice versa.
2. Each participant sees the paired languages and connection state.
3. Push-to-talk captures one finalized utterance and releases microphone resources.
4. The speaker sees the original transcript and both users see the translated subtitle.
5. The recipient can play translated speech and can see an explicit unavailable state if synthesis fails.
6. Critical numeric/date/time mismatches or uncertain supported expressions require speaker confirmation before TTS delivery.
7. The conversation can be resumed from recent history; a participant can review and edit an Outcome Card.
8. Participants can end the session and remove stored conversation data.

## Non-functional requirements

- Mobile-first React/Vite client; FastAPI, WebSockets, Pydantic, SQLAlchemy and SQLite backend.
- Provider credentials remain server-side and are not written to application logs.
- Provider mode is visible and mock mode is never represented as live AI.
- External provider calls have bounded timeouts and generic client-facing errors.
- Production microphone use requires HTTPS/WSS.
- Do not claim accuracy, latency, native-speaker quality, or two-device readiness without measured evidence.

## Acceptance gates

- Unit and integration suite passes, including malformed audio and provider failure behavior.
- Verify actual WAV metadata and browser decode/playback, not merely non-empty audio bytes.
- Confirm Hindi→Telugu and Telugu→Hindi using native spoken utterances, with a native Telugu reviewer.
- Confirm ambiguous amount clarification and reject/confirm paths.
- Complete create/join/speak/translate/hear/reconnect/delete across two physical phones over HTTPS.
- Authenticate sensitive HTTP and WebSocket actions; reject unauthorized participants.
- Document actual provider mode and all remaining limitations.

## Requirement-to-test traceability (current)

| Requirement | Existing evidence | Gap |
|---|---|---|
| Numeric/date/time checks and confirmation | `backend/tests/test_number_parser.py`, `backend/tests/test_meaning_verifier.py`, `backend/tests/test_pipeline.py` | UI and API now explicitly identify the supported-check scope and never claim full translation verification; no broad semantic coverage; Telugu mappings need native review. |
| Room create/join and two-participant event flow | `backend/tests/test_room_e2e.py` | Entire provider pipeline is mocked; currently lacks authorization assertions. |
| Provider fallback and WAV structure | `backend/tests/test_tts_fallback.py` | Newly added tests require full suite execution; no browser audio decode check in automated tests. |
| Responsive UI and audio controls | Frontend build | No frontend interaction or event-render tests. |
| Two physical phones, HTTPS microphone, audible output | None | Manual acceptance run required. |

## Current scope limitation

Meaning Protection now compares supported amounts, dates, times, percentages, recognized measurements, phone-like digit strings with explicit phone context, and other parsed number expressions. It requests speaker confirmation for detected negative/prohibitive statements because the marker rules are provisional. Measurement aliases currently cover common English/SI forms; Hindi/Telugu unit vocabulary and all number-word mappings still need native-speaker review.

This is not general semantic verification. Names, locations, address structure, instruction scope, and contractual terms are not reliably extracted or compared. A matching number does not prove the rest of the sentence is correct. The UI must not present an `ok` result as proof of whole-sentence equivalence.
