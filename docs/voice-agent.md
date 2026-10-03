# Voice agent implementation

The `/voice-assistant` page provides a persistent Hindi/Hinglish or English voice session. The home page and navigation link to it. The manual journey remains available separately.

## Configuration

Set these server-side values in `backend/.env`:

```dotenv
AI_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
# Optional cloud playback; otherwise use a matching device voice.
SARVAM_API_KEY=
SARVAM_TTS_MODEL=bulbul:v3
SARVAM_TTS_VOICE=shubh
```

No Ollama installation or local language model is used by the interviewer. API keys remain on the backend. Speech requires HTTPS in deployment, or localhost during development, and microphone permission. Cloud speech needs its own Sarvam key; the Groq key alone does not provide Hindi playback in this implementation.

## Flow

1. Choose Hindi/Hinglish or English, hear or read the consent notice, and select Agree & start.
2. The microphone stays active. An AudioWorklet keeps short PCM buffers in memory; speech activity and a 1.3-second pause delimit a turn, capped at 25 seconds.
3. Authenticated `/voice/transcribe` sends a WAV turn to Groq Whisper. It rejects oversized audio and high-confidence silence.
4. The existing `/interviews/{id}/turns` endpoint uses `mode: voice` to call the merged interviewer through Groq. Pydantic validates the returned profile. The transaction stores conversation and inferred fields separately for each interview. Provider errors roll back the turn.
5. The client plays the reply through `/voice/speak` with optional Sarvam, or a device voice. Listening resumes automatically. Sustained speech can interrupt playback; the central microphone also interrupts it.
6. When required fields are present, the assistant reads back the profile. A yes after completed playback confirms it. Corrections go through the interviewer again.
7. A separate yes requests recommendations. The assistant describes one result at a time and preserves the distinction between qualification fit and confirmed local availability.
8. Help opens a separate sharing/request confirmation. A stable request ID makes counselor request retries return the same case. No admission or seat is promised.
9. Pause/End releases microphone tracks. Resume reloads the saved interview from the backend. Only the interview ID and referral receipt are stored in sessionStorage by this screen.

Commands include repeat, speak slowly, pause, help, next, details, and request status, with Hindi equivalents. Typing is optional. Explicit confirmation phrases are intentionally restricted to avoid interpreting a correction as approval.

## Implementation boundaries

- This release uses short audio turns over HTTP, not streaming STT or a LiveKit/WebRTC deployment. Turn latency includes upload, recognition, the Groq interview response, and speech generation.
- Activity detection uses an energy threshold and browser echo cancellation. It requires field testing with quiet voices, speakerphone echo, noise, and regional speech. The interrupt button is available when automatic interruption is unreliable.
- Device voice quality and availability vary; configure Sarvam for consistent Hindi playback. Neither provider quality nor regional dialect coverage is guaranteed by this code.
- A connection failure pauses the conversation. Resume restores committed state; the app never fabricates an answer on provider failure.
- The app does not save raw audio. Speech providers process the audio/text under their own account settings and terms.
- IVR/WhatsApp channels and field validation are subsequent work. Worker verification and the existing recommendation model are unchanged.

## Validation

Backend: `python -m pytest tests/test_voice_agent.py tests/test_conversation.py tests/test_interviews.py -q` from `backend` with an isolated SQLite configuration and empty provider keys.

Frontend: `npx tsc --noEmit` and `npm run build` from `frontend`.

Audio unit checks: `node scripts/voice-audio-test.cjs` from `frontend`.

Browser flow: `node scripts/voice-smoke.cjs` from `frontend` against a development server on port 3100. Requires Playwright and Edge; `PLAYWRIGHT_MODULE`, `PLAYWRIGHT_CHANNEL`, and `VOICE_TEST_URL` may override defaults. Audio devices, playback and API responses are mocked: this checks the UI state transitions and confirmation flow, not microphone accuracy. Screenshots go to `frontend/output`.

Before a field release, test actual microphone input, Hindi playback, interruption, denied permissions, expired sessions, and reconnection on target Android devices. Measure response latency and successful completion with representative speakers.

## Merge resolution

Merge commit `426d296` incorporates the interviewer contribution from `origin/feat/llm-interviewer`, retaining the current main application when resolving the branch's divergent backend/dashboard history. The active voice integration uses the existing profile schema and ranking service. The contributed mapper remains available but is not substituted for the application's current recommendation pipeline.

The focused voice/interview suite passes. The existing `test_referrals.py` lifecycle test also fails against the pre-change referral service: it requests a forbidden assigned-to-in_progress transition. The stored referral status constraint also differs from the service's extended lifecycle. This pre-existing worker lifecycle inconsistency needs a separate schema/migration correction; creating and reading counselor requests are covered by the new voice tests.
