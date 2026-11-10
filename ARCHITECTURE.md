# Architecture

## Runtime flow

```text
Phone browser (React)
  microphone → MediaRecorder → decoded/resampled 16 kHz mono WAV
  → room WebSocket → FastAPI
  → Gnani Prisma adapter → translation adapter (Gemini or mock)
  → deterministic supported-entity verifier
  → speaker clarification when required
  → TTS adapter (Gnani, Gemini fallback, or mock)
  → transcript / translation / audio WebSocket events
  → recipient subtitles and user-initiated playback
```

## Components

- `frontend/src/pages`: room entry and conversation screens.
- `frontend/src/hooks`: WebSocket lifecycle and browser audio capture.
- `backend/app/main.py`: HTTP routes, room lifecycle and WebSocket event routing.
- `backend/app/pipeline.py`: finalized-audio processing and delivery state transitions.
- `backend/app/services/{stt,translation,tts}`: interchangeable provider adapters.
- `backend/app/meaning`: deterministic extraction/comparison for amounts, dates, times, percentages, common measurements, phone-like digit strings, other parsed numbers, and provisional negation markers.
- `backend/app/models` and `backend/app/db`: SQLAlchemy records and SQLite engine.

## Message states

`processing → transcribed → translated → awaiting_confirmation | delivered`; confirmed messages move to delivery, rejected messages are not synthesized, and provider failures become `failed`. TTS failure can still leave a translated subtitle available; the UI should clearly state that no audio was delivered.

## Operational boundaries

The meaning verifier only checks extracted critical entities. It cannot prove full-sentence semantics; names, location identity, address structure, instruction scope and contractual terms need separate validation. The current backend stores transcripts, verification metadata, and generated TTS audio in SQLite until deletion/room expiry. Raw input audio is processed in memory and is not persisted by the message model. External providers receive audio or text required for their respective operations. A single-process in-memory WebSocket manager is used; multi-worker deployment needs shared coordination before scaling out.
