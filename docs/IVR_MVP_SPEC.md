# Jeevan Mitra IVR Module Specification (Phase 1 Local Simulator)

## 1. Executive Summary & Purpose

The Jeevan Mitra IVR (Interactive Voice Response) module provides a deterministic, keypad-driven (DTMF) voice-channel access path designed specifically for citizens with basic feature phones (2G/3G keypad phones) and low-connectivity environments. 

### Core Purpose
Enable beneficiaries without smartphones, touch screens, or reliable mobile data connectivity to:
1. Hear affirmative consent notices under the Digital Personal Data Protection (DPDP) Act in Hindi.
2. Explore verified skill training options and government welfare schemes.
3. Check referral and case status without visiting a digital kiosk.
4. Request an asynchronous callback from a human field worker or career counselor.

### Scope and Non-Goals (Phase 1)
- **Non-Goals:**
  - **No live telephony provider:** No Exotel, Twilio, or Plivo integrations in this phase.
  - **No outbound telephone calls:** No live PSTN dialing.
  - **No conversational AI or LLM voice audio:** All menus are deterministic DTMF keypad selections.
  - **No speech-to-text (STT) or text-to-speech (TTS) engines:** Prompts are served as stable prompt keys with standardized Hindi text.
  - **No collection of sensitive identity documents:** No Aadhaar, PAN, bank accounts, biometric data, or OTP collection.
  - **No call recording storage:** Zero audio recordings are stored.
  - **Telephony Cost Disclaimer:** Real phone service requires a paid commercial PSTN telephony provider (such as Exotel or Twilio), an active virtual number (VN), and inbound trunking. It is **not permanently free**. Phase 1 uses **exclusively local mock simulator mode** requiring zero API keys.

---

## 2. Target Persona: The Feature-Phone Beneficiary

- **Demographics:** Rural or semi-urban citizens under PM-AJAY and allied welfare programs, often owning basic KaiOS or numeric-keypad feature phones.
- **Constraints:** Limited literacy, inability to use mobile web browsers or download apps, lack of mobile internet data packs, shared household phones.
- **Behavioral Preferences:**
  - Prefers simple, unambiguous numeric prompts in Hindi (*"Seva jaari rakhne ke liye 1 dabayein"*).
  - High risk of misdialing: requires polite invalid-input retry handling without looping forever.
  - High desire for human support: can press `0` at any decision point to request a field worker callback.

---

## 3. Hindi DTMF Call Tree

```
[ Inbound Call Simulation ]
           │
           ▼
     [ 1. WELCOME ]
     "नमस्ते। जीवन मित्र में आपका स्वागत है।
      सेवा जारी रखने के लिए 1 दबाएं। कॉल समाप्त करने के लिए 2 दबाएं।"
      ├── 1 ──► [ 2. CONSENT ]
      │         "जीवन मित्र आपकी जानकारी का उपयोग केवल सहायता...
      │          सहमति देने के लिए 1 दबाएं। सहमति न देने के लिए 2 दबाएं।"
      │          ├── 1 ──► [ 3. IDENTITY ] (Consent Granted)
      │          │         "अपनी सेवाएं चुनने के लिए 1 दबाएं।
      │          │          फील्ड वर्कर से सहायता के लिए 0 दबाएं।"
      │          │          ├── 1 / 9 ──► [ 4. MAIN MENU ]
      │          │          │             "प्रशिक्षण के लिए 1 दबाएं।
      │          │          │              सरकारी योजनाओं की जानकारी के लिए 2 दबाएं।
      │          │          │              अपने आवेदन या रेफरल की स्थिति के लिए 3 दबाएं।
      │          │          │              फील्ड वर्कर से कॉलबैक के लिए 0 दबाएं।
      │          │          │              मेनू दोबारा सुनने के लिए हैश दबाएं।"
      │          │          │              ├── 1 ──► [ 5. TRAINING MENU ]
      │          │          │              │         ├── 1, 2, 3 ──► Training Detail (Safe Summary)
      │          │          │              │         ├── 0 ──► [ 8. CALLBACK (training_support) ]
      │          │          │              │         └── 9 ──► Main Menu
      │          │          │              ├── 2 ──► [ 6. SCHEMES MENU ]
      │          │          │              │         ├── 1, 2, 3 ──► Scheme Detail (Safe Summary)
      │          │          │              │         ├── 0 ──► [ 8. CALLBACK (scheme_information) ]
      │          │          │              │         └── 9 ──► Main Menu
      │          │          │              ├── 3 ──► [ 7. REFERRAL STATUS ]
      │          │          │              │         ├── 0 ──► [ 8. CALLBACK (referral_status) ]
      │          │          │              │         └── 9 ──► Main Menu
      │          │          │              ├── 0 ──► [ 8. CALLBACK (general_help) ]
      │          │          │              └── # / 9 ──► Repeat Main Menu
      │          │          └── 0 ──► [ 8. CALLBACK (general_help) ]
      │          └── 2 ──► [ 10. GOODBYE ] (Consent Refused - Call Terminates Safely)
      └── 2 ──► [ 10. GOODBYE ] (Call Ends)
```

---

## 4. Complete State Transition Table

| Current State | Input Digit | Next State | Prompt Key | Intent / Action | Accepted Digits |
|---|---|---|---|---|---|
| `welcome` | `1` | `consent` | `CONSENT` | Advance to consent notice | `["1", "2"]` |
| `welcome` | `2` | `goodbye` | `GOODBYE` | Hang up cleanly | `[]` |
| `welcome` | Other / Invalid | `welcome` / `error_retry` | `INVALID_INPUT` / `MAX_RETRIES` | Increment retry counter; if >= 2 go to `error_retry` | `["1", "2"]` / `["0", "2"]` |
| `consent` | `1` | `identity` | `IDENTITY` | Record DPDP consent (`capture_channel='ivr'`) | `["1", "0", "9"]` |
| `consent` | `2` | `goodbye` | `CONSENT_REFUSED` | Record consent refusal, terminate call | `[]` |
| `consent` | Other / Invalid | `consent` / `error_retry` | `INVALID_INPUT` / `MAX_RETRIES` | Increment retry counter | `["1", "2"]` / `["0", "2"]` |
| `identity` | `1` or `9` | `main_menu` | `MAIN_MENU` | Enter main menu options | `["1", "2", "3", "0", "#", "9"]` |
| `identity` | `0` | `callback_request` | `CALLBACK_CONFIRMED` | Queue callback request (`general_help`) | `["2", "9", "#"]` |
| `identity` | `#` | `identity` | `IDENTITY` | Repeat prompt | `["1", "0", "9"]` |
| `main_menu` | `1` | `training` | `TRAINING_MENU` | Load verified training options | `["1", "2", "3", "0", "9", "#"]` |
| `main_menu` | `2` | `schemes` | `SCHEME_MENU` | Load verified scheme options | `["1", "2", "3", "0", "9", "#"]` |
| `main_menu` | `3` | `referral_status` | `REFERRAL_STATUS` | Check referral/case status | `["0", "9", "#"]` |
| `main_menu` | `0` | `callback_request` | `CALLBACK_CONFIRMED` | Queue callback request (`general_help`) | `["2", "9", "#"]` |
| `main_menu` | `#` or `9` | `main_menu` | `MAIN_MENU` | Repeat main menu | `["1", "2", "3", "0", "#", "9"]` |
| `training` | `1`, `2`, `3` | `training` | `TRAINING_DETAIL` | Read safe summary of selected course | `["1", "2", "3", "0", "9", "#"]` |
| `training` | `0` | `callback_request` | `CALLBACK_CONFIRMED` | Queue callback request (`training_support`) | `["2", "9", "#"]` |
| `training` | `9` | `main_menu` | `MAIN_MENU` | Return to main menu | `["1", "2", "3", "0", "#", "9"]` |
| `training` | `#` | `training` | `TRAINING_MENU` | Repeat training menu | `["1", "2", "3", "0", "9", "#"]` |
| `schemes` | `1`, `2`, `3` | `schemes` | `SCHEME_DETAIL` | Read safe summary with official verification disclaimer | `["1", "2", "3", "0", "9", "#"]` |
| `schemes` | `0` | `callback_request` | `CALLBACK_CONFIRMED` | Queue callback request (`scheme_information`) | `["2", "9", "#"]` |
| `schemes` | `9` | `main_menu` | `MAIN_MENU` | Return to main menu | `["1", "2", "3", "0", "#", "9"]` |
| `schemes` | `#` | `schemes` | `SCHEME_MENU` | Repeat schemes menu | `["1", "2", "3", "0", "9", "#"]` |
| `referral_status` | `0` | `callback_request` | `CALLBACK_CONFIRMED` | Queue callback request (`referral_status`) | `["2", "9", "#"]` |
| `referral_status` | `9` | `main_menu` | `MAIN_MENU` | Return to main menu | `["1", "2", "3", "0", "#", "9"]` |
| `callback_request` | `2` | `goodbye` | `GOODBYE` | Clean hangup | `[]` |
| `callback_request` | `9` | `main_menu` | `MAIN_MENU` | Return to main menu | `["1", "2", "3", "0", "#", "9"]` |
| `error_retry` | `0` | `callback_request` | `CALLBACK_CONFIRMED` | Safe exit into worker assistance | `["2", "9", "#"]` |
| `error_retry` | `2` or other | `goodbye` | `GOODBYE` | Safe call termination; prevents infinite loop | `[]` |
| `goodbye` | Any | `goodbye` | `GOODBYE` | Terminal state; session status is `completed` | `[]` |
| `expired` | Any | `expired` | `SESSION_EXPIRED` | Terminal state; session status is `expired` | `[]` |

---

## 5. Privacy, Redaction, and Data Minimization Rules

1. **No Raw Phone Numbers in Logs or Sessions Table:**
   - Raw phone numbers or caller IDs are passed through `hash_caller_reference()` producing a non-reversible SHA-256 hash stored in `caller_reference_hash`.
   - Logging middleware redacts all phone occurrences.
2. **Explicit Affirmative Consent Before Personalization:**
   - Entering `1` in `consent` state invokes `ConsentService.record_consent()` with `capture_channel='ivr'`, `consent_type='dpdp_general'`, and status `granted`.
   - Entering `2` stops all data processing immediately, terminates the call, and refuses consent.
3. **No Cross-Beneficiary Data Leakage:**
   - In `referral_status`, if a caller is anonymous or their phone is unverified, no names, cases, or details are spoken. The system states: *"स्थिति देखने के लिए पहचान आवश्यक है। फील्ड वर्कर से सहायता के लिए 0 दबाएं।"*

---

## 6. Callback Request Behavior & Idempotency Strategy

- **Idempotency per Session:**
  - `ivr_callback_requests` enforces a `UNIQUE(session_id)` constraint.
  - If a caller presses `0` multiple times during the same call session (e.g. from identity, from training, and from error retry), the system retrieves the existing record and does **not** create duplicate open cases.
- **Callback Reasons Captured:**
  - `training_support` (when triggered from training menu)
  - `scheme_information` (when triggered from schemes menu)
  - `referral_status` (when triggered from referral status check)
  - `general_help` (when triggered from identity, main menu, or error retry)
- **Zero Live Telephony Outbound:**
  - Creates an immutable database record for field worker review on their web dashboard. Never executes outbound automated phone calls.

---

## 7. Expiry Strategy & Inactivity Handling

- **Configurable TTL:** Default session TTL is 600 seconds (`IVR_SESSION_TIMEOUT_SECONDS=600`).
- **Deterministic Timeout Enforcement:**
  - Any digit input submitted after `expires_at` transitions session state directly to `expired`, marks `status = 'expired'`, and returns prompt `SESSION_EXPIRED`.
  - Further digits cannot alter session state or mutate data.
- **Explicit Test Endpoint:** `POST /api/v1/ivr/simulate/{session_id}/expire` allows integration tests to verify timeout behavior without waiting.

---

## 8. Future Telephony Provider Boundary (Phase 2 Preview)

The IVR architecture strictly decouples the state machine and service logic from telephony protocols:
- `app.ivr.providers.base.IVRProvider` defines standard protocols for DTMF normalization, webhook validation, and action rendering.
- `app.ivr.providers.mock.MockIVRProvider` implements local JSON-based simulator operation.
- In Phase 2:
  - An `ExotelIVRProvider` will inherit from `IVRProvider`, parse Exotel incoming call XML/JSON webhooks, validate HMAC signatures, and render actions into `<Response><Play>...<Gather>...</Response>`.
  - Audio catalog keys will link to pre-recorded studio `.wav` audio files hosted in object storage.
