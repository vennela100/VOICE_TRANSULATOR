# BharatVaani Live Project State

Updated: 2026-11-10

## Current state

The repository contains a React/Vite client and a FastAPI/SQLAlchemy backend for two-person Hindi↔Telugu rooms. The client records finalized microphone clips, converts them to 16 kHz mono WAV, and sends them over WebSocket. The backend runs STT → translation → supported critical-entity checks → optional speaker confirmation → TTS. Supported checks include amounts, dates, times, percentages, common unit aliases, phone-like digit strings, other parsed numbers and provisional negation markers. Subtitles are sent to both clients; audio playback is user initiated.

## Provider mode observed

The local `backend/.env` selects Gnani for STT and TTS, Gemini for translation (`gemini-3.1-flash-lite` primary, `gemini-3.5-flash-lite` fallback), and contains credentials for both providers.

Latest direct provider checks (verified 2026-11-10):

- **Gemini Translation:** Succeeded translating Hindi to Telugu preserving amounts (Hindi: "सवा लाख रुपये भेज दीजिए" → Telugu: "సవా లక్ష రూపాయలు పంపండి" / spoken: "ఒక లక్ష పాతిక వేల రూపాయలు పంపండి").
- **Gnani Timbre TTS:** Succeeded directly with HTTP 200 generating 199,724 bytes of valid Telugu WAV audio using voice "Suhana".
- **Gnani Prisma STT:** Succeeded directly with HTTP 200 transcribing generated Telugu speech ("సవాలక్ష రూపాయలు పంపండి").
- **Meaning Protection Engine:** Successfully intercepted amount difference (Rs 1,25,000 vs Rs 1,00,000) and triggered the speaker confirmation prompt before delivery.
- **Live HTTPS Tunnel:** Active at `https://pleasant-serves-flux-regarding.trycloudflare.com` enabling physical two-phone browser testing with microphone permissions.

## Environment and repository

- System Python found: 3.10.11; the project virtual environment uses Python 3.11.9 and meets the requirement.
- Node.js: 24.20.0; npm: 12.0.2.
- Git executable is unavailable in the current shell, so repository status and diff cannot be independently checked.
- Latest backend test suite: 102 passed, including concurrent shared SQLite join throttling, room-code collision retry, audio-format reuse, payload limits, Gemini fallback on HTTP/network timeouts, and validated WAV fallback behavior. Latest frontend production build passed with history audio-format playback, rejected-session recovery, and recording auto-stop.
- Audio format is stored with generated audio, returned in room history, and included in delivery events. Startup adds the field to existing SQLite databases.
- Incoming and generated audio are limited to 12 MiB. Transcript, translated display text, and speech text are limited to 4,000 characters.
- Join attempts are recorded with hashed client addresses in SQLite and serialized among workers sharing that database. Trusted reverse-proxy client-address handling remains a deployment task.
- Room creation retries up to five times if the generated code violates the unique database constraint.
- Meaning-check results now carry their supported categories and `overall_meaning_verified: false`; the transcript UI explicitly says passed checks do not verify the full translation. The previous unconditional `language_mapping_verified: true` field has been removed, and parsed number entities now distinguish literal, inferred, provisional and ambiguous mappings. Native review of Hindi and Telugu rules remains outstanding.
- Latest backend suite: 106 passed. Latest Vite production build passed (46 modules; JS 183.20 kB). Frontend event rendering still lacks automated interaction coverage.
- The project has no physical two-device test evidence.
- The local ignored `.env` contains a stable room-token signing secret; read/delete authorization was verified across a backend restart. A deployment must provide its own secret.

## Release assessment

Not ready to call production-ready or demo-validated. Room authorization and SQLite-backed throttling have automated coverage; production proxy address handling, stable deployment secrets, formal security review, and production HTTPS configuration remain open. Highest priority is reliable real Hindi/Telugu provider behavior and the two-phone HTTPS run. See `TASK_BACKLOG.md` and `KNOWN_ISSUES.md`.
