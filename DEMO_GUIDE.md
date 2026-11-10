# Live Demo Guide

## Before the demo

1. Use the documented supported Python and Node versions and install dependencies.
2. Configure Gnani Prisma, Gnani Timbre and translation provider credentials in `backend/.env`; never place keys in the browser.
3. Start the backend and frontend, then check `/api/status`. Treat its output as configuration presence only, not a provider health check.
4. Confirm the displayed provider mode is live, not mock. Current configured TTS can fall back from Gnani to Gemini; disclose that clearly.
5. Expose the frontend through restricted HTTPS so both phone browsers can use microphones.
6. Test the session and deletion path with non-sensitive sample phrases first.

## Two-phone acceptance sequence

1. Phone A creates a Hindi room; Phone B joins with Telugu.
2. Confirm both participants and connection indicators appear.
3. Say a short natural Hindi sentence; verify the original transcript, Telugu subtitle and audible translated playback on Phone B.
4. Reverse directions with a Telugu speaker and Hindi listener.
5. Say an agreed amount expression such as “sava lakh rupaye”; verify a confirmation prompt before translated audio is delivered.
6. Test rejection, reconnection, room access rejection, and end/delete behavior.
7. Record the browser/device, provider modes, utterances, errors, and observed latency. Do not infer model accuracy from one phrase.

## Current status

This checklist has not yet been completed on two physical phones. See `TEST_REPORT.md` and `KNOWN_ISSUES.md`.

The browser automatically ends a recording after 28 seconds to stay below Gnani Prisma REST's documented 30-second clip limit.
