# Local Testing Guide: Jeevan Mitra IVR Simulator

This guide outlines how to interactively test the Phase 1 feature-phone Hindi IVR simulator locally on Windows, macOS, or Linux.
No external telephony provider (Exotel, Twilio, Plivo) and zero external API keys are required.

> [!IMPORTANT]
> **Data Privacy Notice:** All caller references, phone identifiers, and beneficiary records used below are **synthetic test inputs only**. The Jeevan Mitra IVR simulator never returns raw caller references or phone numbers in API responses, event logs, or callback payloads. In the database, caller identifiers are stored exclusively as salted SHA-256 hashes (`caller_reference_hash`), preventing any exposure of plaintext PII.

---

## 1. Prerequisites and Setup

1. **Python Environment**: Python 3.10+ (Verified on Python 3.11).
2. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. **Environment Configuration**:
   In `backend/.env`, confirm:
   ```env
   IVR_PROVIDER=mock
   IVR_DEFAULT_LANGUAGE=hi-IN
   IVR_SESSION_TIMEOUT_SECONDS=600
   IVR_MAX_INVALID_ATTEMPTS=2
   IVR_SIMULATOR_ENABLED=true
   ```
4. **Database Migrations**:
   ```bash
   python -m alembic upgrade head
   ```
5. **Start Local Backend**:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 4000 --reload
   ```
   OpenAPI Swagger Documentation: `http://127.0.0.1:4000/docs`

---

## 2. Standard Manual Training Callback Journey

The standard manual validation journey for a feature-phone user seeking wage-employment training is:

1. **Start** $\rightarrow$ `POST /api/v1/ivr/simulate/start` with symbolic caller reference `TEST_CALLER_A`.
2. **Press 1 at Welcome** $\rightarrow$ Moves from `welcome` to `consent` notice.
3. **Press 1 to Accept Consent** $\rightarrow$ Records affirmative DPDP consent; moves to `identity`.
4. **Press 1 at Identity** $\rightarrow$ Advances to `main_menu`.
5. **Press 1 at Main Menu for Training** $\rightarrow$ Enters `training` catalog (top 3 verified NSQF courses).
6. **Press 0 from Training for Callback** $\rightarrow$ Creates human field-worker callback with reason `training_support`.
7. **Press 2 to Exit** $\rightarrow$ Moves to terminal `goodbye` state with status `completed`.

---

## 3. Interactive PowerShell Script (Windows)

Copy and run this PowerShell snippet to execute the full Journey A flow:

```powershell
# 1. Start IVR call with safe symbolic reference
$startRes = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/start" `
  -Method POST -ContentType "application/json" `
  -Body '{"simulated_caller_reference": "TEST_CALLER_A", "language": "hi-IN"}'

$sessionId = $startRes.session_id
Write-Host "Session Created: $sessionId"
Write-Host "State: $($startRes.state) | Status: $($startRes.status)"

# 2. Press 1 to hear Consent Notice
$step1 = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/$sessionId/input" `
  -Method POST -ContentType "application/json" -Body '{"digit": "1"}'
Write-Host "State: $($step1.state) | Prompt: $($step1.prompt_text)"

# 3. Press 1 to Grant Affirmative DPDP Consent
$step2 = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/$sessionId/input" `
  -Method POST -ContentType "application/json" -Body '{"digit": "1"}'
Write-Host "State: $($step2.state) | Prompt: $($step2.prompt_text)"

# 4. Press 1 from Identity to enter Main Menu
$step3 = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/$sessionId/input" `
  -Method POST -ContentType "application/json" -Body '{"digit": "1"}'
Write-Host "State: $($step3.state) | Prompt: $($step3.prompt_text)"

# 5. Press 1 from Main Menu to enter Training Catalog
$step4 = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/$sessionId/input" `
  -Method POST -ContentType "application/json" -Body '{"digit": "1"}'
Write-Host "State: $($step4.state) | Prompt: $($step4.prompt_text)"

# 6. Press 0 to Request Human Field Worker Callback
$step5 = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/$sessionId/input" `
  -Method POST -ContentType "application/json" -Body '{"digit": "0"}'
Write-Host "State: $($step5.state) | Callback Reason: $($step5.callback_request.callback_reason)"
Write-Host "Callback ID: $($step5.callback_request.id) (Notice: zero phone numbers in response)"

# 7. Press 2 to Conclude Call
$step6 = Invoke-RestMethod -Uri "http://127.0.0.1:4000/api/v1/ivr/simulate/$sessionId/input" `
  -Method POST -ContentType "application/json" -Body '{"digit": "2"}'
Write-Host "State: $($step6.state) | Final Status: $($step6.status)"
```

---

## 4. Equivalent cURL Commands (Bash / Linux / macOS)

### A. Start Call (Request and Safe Response Example)
```bash
curl -s -X POST "http://127.0.0.1:4000/api/v1/ivr/simulate/start" \
  -H "Content-Type: application/json" \
  -d '{"simulated_caller_reference": "TEST_CALLER_A", "language": "hi-IN"}'
```

**Safe API Response (Zero caller reference or phone data returned):**
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
      "text": "नमस्ते। जीवन मित्र में आपका स्वागत है। सेवा जारी रखने के लिए 1 दबाएं। कॉल समाप्त करने के लिए 2 दबाएं।",
      "language": "hi-IN",
      "allowed_digits": ["1", "2"]
    }
  ],
  "retry_count": 0,
  "expires_at": "2026-10-04T15:00:00.000000+00:00",
  "callback_request": null,
  "data_summary": null
}
```

### B. Submit Keypad Input
```bash
curl -s -X POST "http://127.0.0.1:4000/api/v1/ivr/simulate/<SESSION_ID>/input" \
  -H "Content-Type: application/json" \
  -d '{"digit": "0"}'
```

**Safe Callback Response Structure:**
```json
{
  "session_id": "ivrs_a1b2c3d4e5f6",
  "state": "callback_request",
  "status": "active",
  "prompt_key": "CALLBACK_REQUEST",
  "prompt_text": "आपकी कॉलबैक सहायता रिक्वेस्ट दर्ज कर दी गई है। एक फील्ड वर्कर जल्द ही आपसे संपर्क करेंगे। मुख्य मेन्यू के लिए 9 दबाएं। कॉल समाप्त करने के लिए 2 दबाएं।",
  "accepted_digits": ["2", "9", "#"],
  "actions": [
    {
      "action_type": "play_prompt",
      "prompt_key": "CALLBACK_REQUEST",
      "text": "आपकी कॉलबैक सहायता रिक्वेस्ट दर्ज कर दी गई है...",
      "language": "hi-IN",
      "allowed_digits": ["2", "9", "#"]
    }
  ],
  "retry_count": 0,
  "expires_at": "2026-10-04T15:10:00.000000+00:00",
  "callback_request": {
    "id": "icb_f1e2d3c4b5a6",
    "session_id": "ivrs_a1b2c3d4e5f6",
    "beneficiary_id": null,
    "callback_reason": "training_support",
    "status": "requested",
    "created_at": "2026-10-04T15:05:00.000000+00:00"
  },
  "data_summary": null
}
```

### C. Retrieve Session State
```bash
curl -s -X GET "http://127.0.0.1:4000/api/v1/ivr/simulate/<SESSION_ID>"
```

### D. Inspect Session Audit Events
```bash
curl -s -X GET "http://127.0.0.1:4000/api/v1/ivr/simulate/<SESSION_ID>/events"
```

---

## 5. Direct SQLite Database Inspection

Verify that caller phone numbers are never stored in plaintext in the database:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('app.db')
c = conn.cursor()
print('--- SESSIONS (Caller Hash Stored, Never Raw Phone) ---')
for row in c.execute('SELECT id, caller_reference_hash, current_state, status FROM ivr_sessions LIMIT 5'):
    print(row)
print('--- CALLBACK REQUESTS (No Phone Column) ---')
for row in c.execute('SELECT id, session_id, callback_reason, status FROM ivr_callback_requests LIMIT 5'):
    print(row)
print('--- DPDP CONSENTS ---')
for row in c.execute('SELECT id, session_id, capture_channel, status FROM consent_records WHERE capture_channel=\"ivr\" LIMIT 5'):
    print(row)
"
```

---

## 6. Phase 1 Boundaries and Invariants

- **Mock Provider Only:** `IVR_PROVIDER=mock`. No live integration with Exotel, Twilio, Plivo, or cellular carriers.
- **No Inbound/Outbound PSTN Calls:** Audio prompts are served as text responses in JSON for testing.
- **No Webhook Listeners:** No external public HTTPS tunneling (ngrok/Cloudflare) required.
- **No Live External AI/LLM Calls:** Prompts and matching use offline deterministic rule engines.
- **Zero Real Beneficiary Data:** Strictly synthetic persona fixtures.
