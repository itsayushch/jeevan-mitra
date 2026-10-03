# Cloud voice agent

`/voice-assistant` provides a persistent Hindi/Hinglish or English conversation. It uses Groq for speech recognition and the existing structured interviewer, plus streamed cloud neural speech. Speech recognition, the interviewer and speech synthesis use cloud services. A small Silero speech detector runs in the browser on the CPU; no GPU or local LLM is required.

## Setup

Install backend dependencies and restart the backend:

```powershell
cd backend
venv/Scripts/python.exe -m pip install -r requirements.txt
venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 4000
```

Configure `backend/.env` (keys remain on the server):

```dotenv
DATABASE_URL=
DATABASE_PATH=./jeevanmitra.db
AI_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
VOICE_TTS_PROVIDER=edge
VOICE_EN_VOICE=en-IN-NeerjaNeural
VOICE_HI_VOICE=hi-IN-SwaraNeural
ALLOWED_ORIGINS=["http://localhost:3000"]
```

Local development uses `backend/jeevanmitra.db` with SQLite WAL mode. Keep `DATABASE_URL` empty: a nonempty value overrides the local file. Startup creates/migrates and seeds the local database. Existing remote PostgreSQL records are not copied by this configuration change. Voice startup renews invalid/expired browser sessions and clears their stale interview reference so a previous database cannot leave the conversation stuck.

From `frontend`, run `npm install` once and `npm run dev` and open `http://localhost:3000/voice-assistant`. The `predev`/`prebuild` scripts copy the speech detector model and ONNX runtime from installed packages to `public/voice-vad`. These assets are served by this application; the first load includes about 16 MB of model/runtime files. Production needs HTTPS for microphone access and WSS. Include the actual frontend origin in `ALLOWED_ORIGINS`; this also protects WebSocket connections, which are not covered by CORS middleware.

Next's `/api/*` rewrite forwards HTTP and WebSocket traffic to `BACKEND_URL` (default `http://127.0.0.1:4000`). Set that value **before building** if the backend is elsewhere. A reverse proxy in front of Next must forward WebSocket upgrades. A direct browser connection can instead use the frontend build variable:

```dotenv
NEXT_PUBLIC_VOICE_WS_URL=wss://your-backend.example/api/v1/voice/stream
```

The Edge voice adapter uses `edge-tts` and Microsoft's online neural voices without an additional API key. It depends on that online service being reachable; it has no application-level availability guarantee. Provider failures show an error and Repeat retries speech. There is no silent fallback to a robotic device voice. To use the existing Sarvam adapter, set `VOICE_TTS_PROVIDER=sarvam` and `SARVAM_API_KEY`; that adapter returns a complete WAV and does not provide progressive playback.

## RealtimeVoiceChat adaptation

Architecture reference: [KoljaB/RealtimeVoiceChat](https://github.com/KoljaB/RealtimeVoiceChat), inspected at commit `9de323f13371dec2d6269fba0cdcb9254e0ec016`.

We adapted its browser AudioWorklet → WebSocket → cancellable speech → browser playback pattern to the existing FastAPI/Next application. This is our cloud implementation of that architecture; we do **not** run the upstream application or its local RealtimeSTT/RealtimeTTS models. Upstream's default English/local model settings are unsuitable for this cloud Hindi deployment.

### Transport and turn handling

- `VoiceSession` uses browser echo cancellation and Silero v5 speech detection through `@ricky0123/vad-web`. It processes 512-sample frames (32 ms at 16 kHz), so quiet speech can trigger a turn without crossing a fixed loudness threshold. Only detected speech and a 320 ms pre-roll are sent. Silence normally ends a turn after 480 ms, or 1 second in slow mode; a turn is capped at 25 seconds.
- A live microphone meter reads the device independently of speech detection. A muted audio path keeps the browser input graph rendered without microphone playback. Recording, recognition, interview processing and voice buffering have separate statuses. Tap the microphone while recording to finish the answer immediately. Silent, muted, suspended and stalled inputs show microphone recovery guidance instead of remaining at “I’m listening”. The selected input name and a device chooser are available; changing input pauses capture until Resume. Reconnect reopens the input. Tapping the microphone while listening starts a manual answer when automatic detection misses speech; tap again to submit (25-second cap). Physical microphone behavior still needs user verification.
- Database authentication/consent checks run outside the WebSocket event loop. Profile field changes are collected and written in batches while preserving confirmation and revision history.
- `/api/v1/voice/stream` authenticates using a token in its first message, validates origin and processing consent, and keeps buffers/tasks separate per connection. PCM messages include a generation ID. Audio stays in memory. Server logs record completed turn duration and transcription success/failure type, without audio, transcript text or credentials.
- Groq Whisper currently transcribes **completed utterances**. Upload occurs during speech, but this is not streaming word-by-word STT or partial transcription. Recognition tasks are ordered so consecutive answers are not silently discarded.
- The persistent `/interviews/{id}/turns` API uses `mode: voice` and Groq. JSON/Pydantic validation completes before the next question is spoken. LLM tokens are not spoken speculatively; profile updates and permissions remain subject to the existing confirmation rules.
- GPT-OSS 20B/120B models use Groq's strict JSON Schema output for the complete message/profile envelope, with low reasoning effort and a 2,048-token completion budget. Other configured models use JSON object mode and local validation. Malformed/truncated results roll back the turn and return `VOICE_INVALID_RESPONSE` (502). Logs include validation field names/types, never beneficiary values. Provider errors (503) and timeouts (504) have separate messages displayed on the page.
- `edge-tts` emits MPEG frames over the WebSocket as they arrive. `StreamingSpeech` plays them with MediaSource without waiting for the entire file. Browsers lacking MPEG MediaSource support collect the same neural audio and play it as a Blob; those browsers incur extra buffering latency.
- Interruptions cancel the server speech task and immediately clear browser playback. Generation IDs discard late frames. The microphone stays available during recognition, the interview request, and speech. The central microphone button also interrupts.
- The page queues answers received while an earlier interview turn is finishing. An old response cannot reset a new recording. Pause commands act immediately.
- A confirmation prompt counts as heard only after audio playback ends. Interrupted or failed speech cannot authorize profile confirmation or counselor sharing.
- The public `/voice/notice` endpoint speaks a fixed consent notice using the neural voice. It accepts no arbitrary text or beneficiary information.

### Beneficiary flow

1. Choose a language, hear/read the notice, and select Agree & start.
2. Speak naturally; the assistant asks one question at a time.
3. Review the spoken profile and say yes or give a correction.
4. Give separate permission to find pathways. Results distinguish qualification fit from verified local availability.
5. Say help to request counselor support; sharing and submission need a separate yes. A stable request ID prevents duplicate counselor cases.
6. Pause releases microphone tracks and closes the socket. Resume reloads the committed interview from the backend.

Commands include repeat, speak slowly, pause, help, next, details, and request status, with Hindi equivalents. The keyboard remains available.

## Verification

From `backend`:

```powershell
$env:DATABASE_URL=''
$env:GROQ_API_KEY=''
$env:GEMINI_API_KEY=''
venv/Scripts/python.exe -m pytest tests/test_voice_stream.py tests/test_voice_agent.py tests/test_conversation.py tests/test_interviews.py -q
```

The shared recommendation/voice test fixture forces a temporary SQLite database even if a developer has a PostgreSQL URL in `.env`.

From `frontend`: `npx tsc --noEmit`, `npm run build`, `node scripts/voice-audio-test.cjs`, and `node scripts/voice-smoke.cjs`. The smoke test requires Playwright/Edge and a frontend on port 3100. It feeds a synthetic speech fixture through the actual browser AudioContext and Silero detector, while mocking cloud speech playback and APIs to check workflow/confirmation transitions. The fixture contains no beneficiary data. To validate while a dev server is running, set `NEXT_DIST_DIR=.next-voice-check` for the build and server so their output does not collide with `.next`.

`backend/scripts/check_neural_voice.py` benchmarks real Hindi and English neural speech. `frontend/scripts/voice-live-check.cjs` checks actual streaming playback, Groq recognition and the interviewer using synthetic microphone audio, against a separate backend on port 4100. Run that backend with `DATABASE_URL=''`, a temporary `DATABASE_PATH`, real Groq credentials, and `ALLOWED_ORIGINS` including `http://localhost:3100`. Start a built frontend on port 3100. The script redirects its test requests to that isolated backend. `PLAYWRIGHT_MODULE`, `VOICE_TEST_URL` and `VOICE_TEST_BACKEND` can override defaults.

Measured during development: first neural audio arrived in 1.64 seconds for English and 1.04 seconds for Hindi in two short provider probes. One live English browser turn began reply playback 2.85 seconds after the synthetic recording and trailing silence finished. A Hindi browser turn began reply playback 2.65 seconds after the synthetic speech finished, including the silence wait. These are individual observations, not service guarantees or a before/after benchmark.

After the Silero change, live browser checks detected synthetic speech at 20% volume and began playing the reply 3.56 seconds after speech ended in English and 2.33 seconds in Hindi, including the silence wait. The local SQLite connection plus three small queries took 2.87 ms in one check; the former remote database took about 3.34 seconds including connection setup. These are separate observations, not a controlled end-to-end comparison.

Physical microphones, speaker echo, regional accents and unstable mobile networks still need field checks. Speech detection uses pauses, not semantic understanding of whether a person has finished speaking. The completed-utterance STT → validated LLM response → TTS pipeline still introduces cloud latency. The app does not save raw audio; external speech providers process the supplied audio/text.

## Existing integration

Merge commit `426d296` incorporates the `feat/llm-interviewer` contribution while retaining the current application across divergent branch changes. Groq remains the interviewer provider and the existing recommendation pipeline remains authoritative.

The pre-existing referral lifecycle test requests a forbidden assigned-to-in_progress transition; the database status constraint also differs from the service's extended lifecycle. Creating and reading counselor requests are covered by the voice tests. That separate lifecycle migration is outside this voice change.
