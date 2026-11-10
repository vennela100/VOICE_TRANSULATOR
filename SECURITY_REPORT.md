# Security and Privacy Report

Updated: 2026-11-10

## Review findings

The read-only review found sensitive room actions accessible using a room code without participant authorization. The WebSocket URL used room and participant identifiers without a separate capability token. CORS allowed every origin with credentials enabled, and the application debug setting defaulted on. Six-character room codes use non-cryptographic randomness and join attempts are not rate limited. These are release blockers for a public tunnel.

Sensitive room reads/writes/deletion now require a signed, room-scoped participant capability. WebSocket participants must authenticate before joining room broadcasts. Only the room creator can delete the room. CORS is configured from `CORS_ALLOWED_ORIGINS`, credentials are disabled, and debug defaults off. Room-join attempts are limited to 10 per 10 minutes using SHA-256 hashed client addresses stored in SQLite; `BEGIN IMMEDIATE` serializes reservations among workers sharing the same SQLite file. Room-code uniqueness conflicts are retried up to five times. Provider exception details are not returned to the client. Automated tests cover route throttling, shared limiter state across instances, concurrent reservations over separate SQLite connections, and code-collision retry.

The token signing key falls back to a process-local random value when `ROOM_TOKEN_SECRET` is empty. The local ignored `.env` now contains a generated stable secret, and an authenticated room read/delete succeeded after restarting the backend. Set a separate stable high-entropy secret in every deployed instance; otherwise active sessions stop working after restart and multi-worker instances will reject one another's tokens. Set a trusted HTTPS/WSS deployment origin before phone testing.

## Data handling

- Raw input audio is sent to the selected STT provider and is not stored in the message table.
- Original/translated transcripts, verification details and generated speech audio are stored temporarily in SQLite.
- Outcome summary generation may send transcript text to the configured summarization provider.
- The landing screen now discloses provider processing and temporary generated-audio retention.
- Do not use real sensitive conversations in the demo until consent and retention language are clear.

## Release status

Not approved for production exposure. A temporary Cloudflare quick tunnel is active at the user's request for phone testing; it has no uptime guarantee and anyone with its link can reach the app. Shared join throttling requires every worker to use the same SQLite database. The app currently keys the limit from the ASGI client address and does not trust forwarded-IP headers; production must set up a trusted proxy boundary and verify client-address handling. Codes remain six characters and can be guessed within the throttled window. There is no formal penetration test or dependency audit. Capabilities are bearer credentials held in session storage and should be protected against XSS. The room UI now stops retrying permanently rejected session tokens and presents a recovery message. No production deployment has been performed.
