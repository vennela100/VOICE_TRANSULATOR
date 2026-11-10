# Known Issues

- Live Gnani Timbre returned HTTP 500 for short Hindi and Telugu synthesis checks. Gemini TTS fallback produced valid WAV for both; delivery to a real phone remains unvalidated.
- Live Gemini Hindi→Telugu translation succeeded through the fallback after the primary returned a server error; Telugu→Hindi succeeded on the primary in the latest check. Availability and latency remain intermittent and unbenchmarked.
- Gnani Prisma returned non-empty transcripts for Gemini-generated Hindi and Telugu clips, but neither matched the source sentence. Native Hindi/Telugu speaker recordings and quality review are required before claiming accuracy.
- No physical two-phone test has been performed.
- Meaning Protection checks selected numeric/time categories and provisional negation markers, but it does not prove sentence-level meaning equivalence. Spoken number mappings are labeled inferred/provisional; Hindi and Telugu number/unit rules still need native review. Names, locations, address structure, instruction scope and contractual terms are unsupported.
- Existing E2E tests use mock providers and do not validate audio container correctness or browser playback.
- Audio playback is user initiated. Browser autoplay is not relied upon.
- Backend relies on in-memory WebSocket coordination and is not ready for multi-worker scaling.
- Join-by-code attempts are throttled to 10 per 10 minutes using hashed client addresses in SQLite; workers share the limit only when configured with the same SQLite database. A reverse proxy must be configured to provide a trustworthy client address; the app does not trust forwarded-IP headers. Six-character room codes remain guessable. The local ignored `.env` has a stable `ROOM_TOKEN_SECRET`; production deployment must set its own stable secret.
- System Python detected in this shell is 3.10.11; project documentation requires Python 3.11+.
- Git executable is unavailable in the current shell, preventing status/diff verification.
