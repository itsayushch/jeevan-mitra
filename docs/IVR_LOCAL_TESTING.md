# Local Testing Guide: Jeevan Mitra IVR Simulator

This guide outlines how to test the Phase 1 feature-phone IVR simulator locally on Windows, macOS, or Linux. No external telephony provider (Exotel/Twilio) and zero external API keys are required.

---

## 1. Prerequisites

- Python 3.10+ (tested on Python 3.11)
- Activated virtual environment
- Installed dependencies: `pip install -r backend/requirements.txt`

---

## 2. Environment Configuration

In `backend/.env` (or via environment variables), verify:

```env
IVR_PROVIDER=mock
IVR_DEFAULT_LANGUAGE=hi-IN
IVR_SESSION_TIMEOUT_SECONDS=600
IVR_MAX_INVALID_ATTEMPTS=2
IVR_SIMULATOR_ENABLED=true
```

---

## 3. Database Migration

The IVR persistence schema is managed via Alembic:

```bash
cd backend
python -m alembic upgrade head
```

This applies migration `a1b2c3d4e5f6_ivr_tables.py` creating:
- `ivr_sessions`
- `ivr_events`
- `ivr_callback_requests`

---

## 4. Starting the Backend Server

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

Interactive OpenAPI docs will be available at:
`http://localhost:4000/docs`

---

## 5. Automated Test Execution

Run the complete test suite:

```bash
# Run all IVR unit, service, and API integration tests
python -m pytest backend/tests/test_ivr_engine.py backend/tests/test_ivr_service.py backend/tests/test_ivr_api.py -v

# Run existing core test suites to confirm no regressions
python -m pytest backend/tests/test_consents.py backend/tests/test_referrals.py backend/tests/test_auth.py -v
```

---

## 6. Example cURL Commands

### A. Start a Simulated IVR Call

```bash
curl -X POST "http://localhost:4000/api/v1/ivr/simulate/start" \
  -H "Content-Type: application/json" \
  -d '{
    "simulated_caller_reference": "9876543210",
    "language": "hi-IN"
  }'
```

**Expected Response (HTTP 201 Created):**
```json
{
  "session_id": "ivrs_a1b2c3d4e5f6",
  "state": "welcome",
  "status": "active",
  "prompt_key": "WELCOME",
  "prompt_text": "नमस्ते। जीवन मित्र में आपका स्वागत है। सेवा जारी रखने के लिए 1 दबाएं। कॉल समाप्त करने के लिए 2 दबाएं।",
  "accepted_digits": ["1", "2"],
  "actions": [
    {
      "action_type": "play_prompt",
      "prompt_key": "WELCOME",
      "text": "नमस्ते। जीवन मित्र में आपका स्वागत है।...",
      "language": "hi-IN",
      "allowed_digits": ["1", "2"]
    }
  ],
  "retry_count": 0,
  "expires_at": "2026-10-04T13:45:00.000000+00:00"
}
```

### B. Submit Keypad Digit Input

Replace `{session_id}` with the returned session ID:

```bash
curl -X POST "http://localhost:4000/api/v1/ivr/simulate/{session_id}/input" \
  -H "Content-Type: application/json" \
  -d '{
    "digit": "1",
    "idempotency_key": "step_1"
  }'
```

### C. Retrieve Active Session Details

```bash
curl -X GET "http://localhost:4000/api/v1/ivr/simulate/{session_id}"
```

### D. View Audit Event History

```bash
curl -X GET "http://localhost:4000/api/v1/ivr/simulate/{session_id}/events"
```

### E. Manually Expire Session (Testing Helper)

```bash
curl -X POST "http://localhost:4000/api/v1/ivr/simulate/{session_id}/expire"
```

---

## 7. Complete End-to-End Walkthrough Scenario

**Goal:** Caller initiates call, grants DPDP consent, navigates to training options, requests a worker callback, and hangs up cleanly.

1. **Step 1: Start Call**
   - Call `POST /api/v1/ivr/simulate/start`
   - State: `welcome`
   - Prompt: *"नमस्ते। जीवन मित्र में आपका स्वागत है... सेवा जारी रखने के लिए 1 दबाएं।"*

2. **Step 2: Accept Service Continuation (Press 1)**
   - Call `POST /api/v1/ivr/simulate/{session_id}/input` with `{"digit": "1"}`
   - State: `consent`
   - Prompt: *"जीवन मित्र आपकी जानकारी का उपयोग केवल सहायता... सहमति देने के लिए 1 दबाएं।"*

3. **Step 3: Grant Affirmative Consent (Press 1)**
   - Call `POST /api/v1/ivr/simulate/{session_id}/input` with `{"digit": "1"}`
   - State: `identity`
   - Side effect: DPDP affirmative consent record persisted in `consent_records` (`capture_channel='ivr'`).
   - Prompt: *"अपनी सेवाएं चुनने के लिए 1 दबाएं। फील्ड वर्कर से सहायता के लिए 0 दबाएं।"*

4. **Step 4: Go to Main Menu (Press 1)**
   - Call `POST /api/v1/ivr/simulate/{session_id}/input` with `{"digit": "1"}`
   - State: `main_menu`
   - Prompt: *"प्रशिक्षण के लिए 1 दबाएं। सरकारी योजनाओं की जानकारी के लिए 2 दबाएं..."*

5. **Step 5: Select Training (Press 1)**
   - Call `POST /api/v1/ivr/simulate/{session_id}/input` with `{"digit": "1"}`
   - State: `training`
   - Prompt: *"आपके लिए उपलब्ध प्रशिक्षण विकल्प सुने..."*

6. **Step 6: Request Field Worker Callback (Press 0)**
   - Call `POST /api/v1/ivr/simulate/{session_id}/input` with `{"digit": "0"}`
   - State: `callback_request`
   - Side effect: `ivr_callback_requests` record created with `callback_reason='training_support'`.
   - Prompt: *"आपकी कॉलबैक सहायता रिक्वेस्ट दर्ज कर दी गई है... कॉल समाप्त करने के लिए 2 दबाएं।"*

7. **Step 7: Conclude Call (Press 2)**
   - Call `POST /api/v1/ivr/simulate/{session_id}/input` with `{"digit": "2"}`
   - State: `goodbye`
   - Status: `completed`
   - Prompt: *"जीवन मित्र से संपर्क करने के लिए धन्यवाद। नमस्ते।"*

---

## 8. Troubleshooting

- **403 Forbidden with `SIMULATOR_DISABLED`:**
  Ensure `IVR_SIMULATOR_ENABLED=true` in `backend/.env`.
- **422 Validation Error on Digit:**
  The `digit` field must be a string containing a single DTMF character (`"0"` through `"9"`, or `"#"`). Multi-digit strings like `"12"` or alphabetic characters are rejected.
- **Session Expired on Input:**
  Check `IVR_SESSION_TIMEOUT_SECONDS`. By default, sessions expire after 10 minutes (600 seconds) of inactivity.
- **No Results in Training/Schemes:**
  Run `python backend/app/database.py` or seed the database with initial qualification and training course data.
