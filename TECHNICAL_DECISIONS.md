# Technical Decisions

| Decision | Rationale and current consequence |
|---|---|
| Finalized push-to-talk clips for MVP | Simpler turn-taking and failure recovery than streaming; adds end-of-utterance latency. |
| Gnani Prisma REST adapter | [Official REST docs](https://docs.gnani.ai/api/STT/speech-to-text) specify `POST https://api.vachana.ai/stt/v3`, `X-API-Key-ID`, multipart `audio_file` and `language_code`; clips are limited to 30 seconds. [Supported language docs](https://docs.gnani.ai/api/STT/languages) list Hindi and Telugu. Live Gemini-generated Hindi and Telugu samples produced non-matching transcripts, so native-speaker device validation is still required. |
| Gnani Timbre REST adapter | [Official REST docs](https://docs.gnani.ai/api/TTS/tts-inference) specify `POST https://api.vachana.ai/api/v1/tts/inference`, Timbre v2.5 and WAV configuration; the [voice catalog](https://docs.gnani.ai/api/TTS/available-voices) lists Nalini for Hindi and Suhana for Telugu. Live Hindi and Telugu requests returned HTTP 500; configured Gemini TTS fallback returned valid WAV for both. |
| Gemini translation adapter | Translation is provider-independent behind an interface, uses a 45-second per-model request timeout, and attempts a secondary model for retryable primary status codes. Live Hindi→Telugu succeeded on fallback and Telugu→Hindi on primary; no quality or latency guarantee is inferred from these samples. |
| SQLite and single-process WebSocket manager | Fits local MVP; horizontal scaling requires migrations and shared room/event state. |
| Deterministic supported entity checks | Keeps supported numeric/date/time decisions inspectable; this is not broad semantic verification and native-language validation is outstanding. |
| No silent mock substitution | Mock providers are explicitly selected and surfaced as simulation mode; they are not a live integration fallback. |
