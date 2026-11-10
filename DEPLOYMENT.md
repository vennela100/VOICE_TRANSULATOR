# Deployment Preparation

## Local development

Use Python 3.11+ and Node.js 18+. Install backend requirements and frontend npm dependencies as described in `README.md`. Run FastAPI on port 8000 and Vite on port 3000.

## Two-phone development demo

Phone browsers require a secure context for microphone access. Use an HTTPS tunnel to the Vite frontend with `/api` and `/ws` proxied to the backend. Keep the tunnel restricted to intended participants. Do not expose the current application publicly until participant authorization and CORS remediation is verified.

## Production preparation gaps

- Restrict CORS to the deployed frontend origin and disable debug.
- Set a stable high-entropy `ROOM_TOKEN_SECRET` consistently on all backend workers; generate one with `py -3.11 -c "import secrets; print(secrets.token_urlsafe(32))"` and store it in a secret manager.
- Use TLS for HTTPS/WSS and secure provider secret storage.
- Add database migrations, backups, health/readiness checks, structured metrics and rollback steps.
- Validate rate limits, privacy retention, provider quotas and data disclosures.
- Run the physical two-phone acceptance checklist in `DEMO_GUIDE.md` before release.

No production deployment has been performed. A temporary Cloudflare quick tunnel is currently running for user testing and should be stopped after the test session.
