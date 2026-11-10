# BharatVaani Live

**Your Language. Your Voice. One Conversation.**

Multi-language (English + 11 Indian languages: Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Urdu), two-person, push-to-talk web conversations with finalized speech recognition, translation, subtitles and speech playback. Deterministic checks cover selected amounts, dates, times, percentages, measurements, numbers and phone-like identifiers; provisional negation markers require speaker confirmation. These checks do not verify complete sentence meaning.

## Current implementation

- Six-character create/join rooms, language selection, phone-friendly React client, and room WebSockets.
- Browser recording converts finalized MediaRecorder audio to 16 kHz mono WAV.
- Provider interfaces for Gnani Prisma v2.5 speech recognition, Gnani Timbre v2.5 primary speech output, and Gemini text translation. When Gemini is configured, its real TTS service is an explicit fallback if Gnani Timbre returns unusable audio; this fallback is identified in status and is not a mock.
- Meaning checks run before speech synthesis. Spoken number mappings are labeled inferred or provisional rather than verified; Telugu word-number mappings, Hindi colloquial fractions, and detected negations ask the speaker to confirm. Native-language review remains outstanding for Hindi and Telugu number and unit rules. Names, locations, address structure and instruction scope are not fully verified.
- Confirmation/re-record flow, one-time TTS delivery per message ID, recent-history resync, editable outcome card, room deletion, and configurable expiry.
- A generated 100-row text corpus and an evaluation harness are included. These are not real recordings or measured model results.

## Requirements

- Windows PowerShell
- Python 3.11+
- Node.js 18 or newer

## Install

Run from the project directory:

```powershell
if (-not (Test-Path backend\.env)) { Copy-Item .env.example backend\.env }
py -3.11 -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location frontend
npm install
Set-Location ..
```

Edit `backend\.env` with Notepad. Never paste provider keys into frontend files or chat. `mock` is the safe default and is clearly labeled in the app. Mock providers simulate the flow; they do not demonstrate real recognition, translation, or speech quality.

Set `ROOM_TOKEN_SECRET` to a stable high-entropy value before deployment. Sensitive room routes and WebSockets require the participant capability issued at create/join. The room creator can end/delete the session. Set `CORS_ALLOWED_ORIGINS` to the trusted frontend origin; do not expose the API through a public tunnel until the deployment security checklist is complete.

Generate a signing secret with `py -3.11 -c "import secrets; print(secrets.token_urlsafe(32))"`, then store it only in `backend\.env` or a secret manager. Local development uses an ephemeral process secret when it is unset, which invalidates existing room tokens after a backend restart.

For live providers, configure the backend `.env`:

```dotenv
STT_PROVIDER=gnani
TTS_PROVIDER=gnani
TRANSLATION_PROVIDER=gemini
GNANI_API_KEY_ID=your-Gnani-key-id
GEMINI_API_KEY=your-Gemini-key
```

Prisma uses the documented `https://api.vachana.ai/stt/v3` endpoint and defaults to Prisma v2.5. Timbre uses the documented `/api/v1/tts/inference` endpoint with Hindi Nalini and Telugu Suhana voices. Gemini model selection is configurable with `GEMINI_MODEL`. The backend sends credentials only to provider services. If the keys are unavailable, leave the matching providers in mock mode.

Gnani credentials activate Prisma transcription and Timbre speech synthesis. Gemini handles translation and can synthesize fallback speech when Timbre fails; it is not used as a replacement for the Gnani STT integration.

## Run locally

Backend PowerShell window:

```powershell
Set-Location C:\Users\alamu\Downloads\gnani_ai\bharatvaani\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend PowerShell window:

```powershell
Set-Location C:\Users\alamu\Downloads\gnani_ai\bharatvaani\frontend
npm run dev -- --host 0.0.0.0
```

Open `http://localhost:3000` on the development computer. For two phones, expose the Vite port through an HTTPS tunnel (phone browsers require a secure origin for microphone access); the Vite proxy forwards `/api` and `/ws` to the local backend. Do not share the tunnel address publicly beyond the intended demo participants. API docs are at `http://localhost:8000/docs`.

## Verification

```powershell
Set-Location C:\Users\alamu\Downloads\gnani_ai\bharatvaani\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe eval\build_test_set.py
.\.venv\Scripts\python.exe eval\evaluate.py
```

The evaluation harness prints `null` for metrics without measurements; it does not invent values. Copy `eval\results_template.csv` to `eval\results.csv` and fill it with actual utterance runs. Use `eval\translation_rating_sheet.csv` for human ratings. `eval\native_language_review.md` describes the Telugu review that is still needed.

## Demo checklist

1. Configure live Prisma, Timbre, and a translation provider in `backend\.env`; restart the backend and check `http://localhost:8000/api/status`.
2. Open the HTTPS frontend on both phones. Create a Hindi room on one and join with Telugu on the other.
3. Speak a short finalized sentence. Check both devices show original and translated subtitles and that the listener can play the synthesized audio.
4. Say “sava lakh rupaye”. The speaker should see a confirmation prompt for Rs 1,25,000. Confirm to deliver once; reject to keep it undelivered and re-record.
5. Open the outcome card, review/edit its details, save, then end and delete the session.

The current local environment has provider keys configured, but a full live two-phone run, native Telugu review, and measured evaluation recordings remain outstanding. The project is not yet demo-validated by the stated definition. Do not report accuracy or latency until the evaluation file contains measured runs. See `PROJECT_STATE.md`, `TEST_REPORT.md`, and `KNOWN_ISSUES.md` for current evidence.
