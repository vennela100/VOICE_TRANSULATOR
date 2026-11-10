# Test Report

Updated: 2026-11-10

## Recorded evidence

- Backend: `144 passed` in `backend/.venv/Scripts/python.exe -m pytest -q` including 38 new multilingual validation tests (`test_multilingual.py`) covering all 12 supported Indian languages & English across STT language codes, Timbre voice catalogs, Gemini translation names, and participant request validation.
- Frontend: Vite production build passed with multi-language selector grid (`vite v5.4.21`, 46 modules; output JS 183.94 kB).
- Browser audio: fake microphone capture, WAV conversion and `play()` completion were exercised in a headless browser. No physical microphone or human audibility check was performed.
- Direct providers (2026-11-10): live Gemini translation succeeded for Hindi→Telugu through the fallback after the primary returned `ServerError`; Telugu→Hindi succeeded. Gnani Timbre returned HTTP 500 for both Hindi and Telugu short phrases; Gemini TTS fallback returned valid WAV (172,844 and 126,764 bytes). Gemini-generated Hindi and Telugu clips sent to Gnani Prisma both returned non-empty transcripts, but neither matched the source sentence. These synthetic clips are not native-speaker accuracy evidence.
- Local runtime: frontend returned HTTP 200. The backend status endpoint reports Gnani STT/TTS and Gemini translation configured; this reports configuration, not provider health.
- Temporary HTTPS tunnel: a fresh quick tunnel returned HTTP 200 from `/api/status`. Two automated clients previously created/joined a room over HTTPS, authenticated over WSS, received `room.state`, and observed `participant_joined`; the creator deleted the test room. This validates tunnel/API/WebSocket routing, not two physical phones or real audio.
- Meaning Protection tests cover cross-script percentage mismatches, English unit aliases, quantity changes, phone-like digit formatting, provisional Hindi/Telugu negation markers, and hold-before-TTS when a measurement or negative instruction changes.
- The verifier returns the exact supported-check scope and always sets `overall_meaning_verified` to false. The UI labels passing results as limited critical-detail checks and warns that the full translation is not verified.
- Number parser/entity results no longer label Hindi word mappings as verified; they carry mapping statuses. Native Hindi and Telugu review remains pending.
- Audio format regression test verifies persisted non-WAV format metadata is reused on cached delivery.
- Conversation history now passes backend `audio_format` into the audio player, with a WAV default for older records.
- Payload-limit tests verify oversized translated text stops before TTS and oversized synthesized audio leaves a truthful text-only delivery state. Incoming audio is limited to 12 MiB before and after base64 decoding.
- Join authorization tests verify the 10-attempt limit, persistence across limiter instances, and that concurrent reservations from separate SQLite connections cannot exceed the limit. This is a thread/connections test, not a multi-process deployment stress test.
- Room creation test forces a duplicate code and verifies retry uses a fresh code.
- Local runtime restarted with a stable ignored `.env` signing secret; an authenticated room read and creator deletion both succeeded using a token issued before the restart.
- WebSocket client now stops retrying on server close codes 4401/4404 and shows an expired/ended room message. The frontend build passed, but a browser-level close-code interaction test is still missing.
- Provider fallback tests cover translation 429/5xx and connection/read timeouts, fallback timeout, TTS timeout, TTS 429/503 responses, invalid WAV, unvalidated MP3, and safe dual-provider failure.
- The browser auto-stops recordings at 28 seconds against the Gnani Prisma REST documentation's 30-second clip limit. The UI message and production build were checked; no physical microphone timer test was performed.

## What these results do not prove

- Live Hindi↔Telugu translation quality or reliable real-time provider availability.
- Gnani Timbre availability for the configured account.
- Real microphone behavior or audible playback on either physical phone.
- Complete protection of names, negation, instructions, addresses, phones, or all numeric expressions.
- Production security, performance, or deployment readiness.

## Next verification run

Complete real Hindi and Telugu native-speaker recordings and two-phone HTTPS acceptance. Add native-speaker review for Meaning Protection rules, formal schema migration tooling, and frontend interaction coverage. Do not report these as passed until executed.
