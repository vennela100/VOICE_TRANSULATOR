# Changelog

## Unreleased

- Expanded language support from Hindi & Telugu to 12 languages: English + 11 Indian languages (Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Urdu).
- Mapped Gnani Prisma v2.5 / v3.0 STT language codes across all 12 languages.
- Configured Gnani Timbre v2.5 voice catalog (Nalini, Suhana, Kaveri, Pranav) and language codes across all 12 languages with Gemini TTS fallback.
- Added comprehensive language translation mapping in Gemini Translation adapter for all language pairs.
- Upgraded frontend `LanguageSelector` to responsive multi-language grid featuring native scripts and English labels.
- Added 38 multilingual integration tests (`tests/test_multilingual.py`); total test suite increased from 106 to 144 passing tests.

- Added explicit real Gemini TTS fallback when Gnani Timbre fails and Gemini credentials are configured.
- Added Gemini translation model fallback for transient service failures.
- Improved WebSocket reconnect lifecycle handling.
- Added signed room-scoped participant authorization, creator-only room deletion, join throttling and cryptographically selected room-code characters.
- Restricted CORS defaults, disabled debug by default, and sanitized client-facing provider errors.
- Clarified provider/fallback mode, translation progress and audio playback errors in the UI.
- Expanded Meaning Protection with percentage, unit, phone-like number, generic number and provisional negation checks that hold speech until confirmation when needed.
- Persisted synthesized audio format through SQLite, history and delivery events so cached audio keeps its correct playback type.
- Enforced 12 MiB audio and 4,000-character transcript/translation limits.
- Added regression coverage for saved audio format, cached delivery and payload limits.
- Added explicit limited-meaning-check status to translation events and transcript UI; removed an unconditional language-mapping verification claim.
- Number entities now report literal, inferred, provisional or ambiguous mapping status rather than a boolean that implied native validation.
- Transcript bubbles warn when a spoken number was interpreted from words and should be checked with the speaker.
- Made join throttling persist hashed client-address attempts in SQLite, shared by workers using the same database.
- Added bounded retry when a generated room code collides with the SQLite unique constraint.
- Configure a 45-second Gemini translation request timeout and fall back to Gemini speech when Gnani raises or returns unusable audio.
- Add failure-mode tests for translation and TTS fallback across timeouts, rate limits and provider errors.
- Corrected conversation history to pass the stored audio format to the playback control.
- Stop WebSocket retry loops after permanent room/auth rejection and show an actionable expired-session message.
- Added project state, requirements, architecture, API, schema, decisions, test, security, demo and deployment documentation.
- Participant authorization and CORS fixes have automated coverage; formal penetration testing and production hardening remain open. See `SECURITY_REPORT.md`.
# Unreleased

- Gemini translation now uses its fallback model for HTTP and network timeouts; active TTS fallback accepts only structurally valid WAV output.
- Added provider fallback regression coverage; backend suite now passes 102 tests.
