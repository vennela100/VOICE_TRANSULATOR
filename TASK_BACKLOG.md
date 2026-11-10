# Task Backlog

## P0 — before sharing a demo tunnel

- [x] Authenticate sensitive room HTTP routes and WebSocket participant actions; test unauthorized access.
- [x] Restrict CORS and production debug settings; use HTTPS/WSS for phone microphone access. HTTPS/WSS is live via Cloudflare Tunnel.
- [x] Show a clear translated-text-only state when TTS fails; avoid labeling subtitles-only as audio delivered.
- [x] Verify live provider pipeline (Gnani Prisma STT, Gnani Timbre TTS, Gemini Translation, Meaning Engine).
- [ ] Complete live two-phone physical demo verification.

## P1 — demo reliability

- [ ] Add native Telugu review of number-word rules and expand reviewed utterance set.
- [ ] Test WAV file structure and browser playback; E2E currently checks non-empty mock bytes only.
- [x] Make playback state and browser playback errors visible in the conversation UI.
- [x] Validate translation and TTS fallback with simulated timeout, rate-limit and service-error responses; live Gemini TTS fallback returned valid WAV after Gnani HTTP 500.
- [x] Route Gemini translation transport timeouts through its fallback model and reject unvalidated non-WAV output in the active TTS fallback chain.
- [x] Remove unearned full-meaning/language-mapping verification labels; expose supported-check scope and number mapping status in API and transcript UI.
- [x] Persist synthesized audio format and return it consistently in history and delivery events.
- [x] Enforce 12 MiB input/output audio limits and 4,000-character transcript/translation limits.
- [x] Auto-stop browser recordings at 28 seconds to stay under Gnani Prisma REST's documented 30-second clip limit.
- [ ] Add frontend interaction tests and end-to-end test over HTTPS on two devices.
- [x] Store hashed room-join attempts in SQLite and serialize reservations so workers sharing the database share the throttle.
- [x] Retry room-code collisions up to five times using the database unique constraint.
- [x] Use cryptographically secure room-code character selection and retry collisions.

## P2 — production readiness

- [ ] Add schema migration tooling, shared room/event coordination, metrics and health checks.
- [ ] Design consent, retention, encryption-at-rest, and provider data disclosures.
- [ ] Measure latency and reliability with a labeled bilingual recording set; report uncertainty and native-speaker ratings.
- [ ] Obtain native Hindi/Telugu review for numeric, unit and negation mappings; add reviewed address/phone/name/location coverage and instruction-scope checks. Preserve explicit uncertainty for unsupported semantics.
