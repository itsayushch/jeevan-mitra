# Must-Have Features — PM-AJAY AI Livelihood Voice Assistant

> Product and implementation specification based on `PM-AJAY-AI-Voice-Assistant.pdf`. This is an independent prototype, not an official government service. The first release uses a lightweight web experience; external communication channels and institutional integrations are future phases.

## 1. Product goal

Help people describe their education, skills, interests, constraints, and work preferences in natural language, then provide explainable, source-linked NSQF qualification suggestions and practical next steps. Recommendations are guidance, not eligibility decisions, training-seat confirmations, job offers, or subsidy approvals.

**Primary users:** beneficiaries with limited digital literacy and counselors helping them. **Initial scope:** one pilot district, a small verified catalog, Hindi and English interfaces, and text-first interaction with optional voice. Expand coverage only after testing.

**Core journey:** Open site → choose language → review consent notice → talk or type about background → review and correct extracted profile → see 2–3 relevant pathways with reasons, skill gaps, source links, and availability caveats → print a summary or seek human help.

## 2. Product principles

- [ ] Make every essential task possible through text even if microphone, speech synthesis, or AI is unavailable.
- [ ] Keep the interface mobile-first, low-bandwidth, accessible, and respectful; ask one short question at a time.
- [ ] Label examples and unverified information clearly. An NQR qualification is not proof that a course or vacancy exists nearby.
- [ ] Show official source links and `last_verified_at` for qualification, opportunity, and scheme information.
- [ ] Request consent before saving a profile or sending answers to an AI service. Allow guest use, correction, deletion, and a clear explanation of data handling.
- [ ] Do not request Aadhaar, bank details, a caste certificate, phone number, or exact address for the prototype.
- [ ] Do not infer a person's community from their name, accent, occupation, or location. Avoid storing sensitive identity attributes unless necessary for a separately authorized workflow.
- [ ] Ask clarifying questions when an answer is uncertain; do not silently invent or overwrite a profile field.
- [ ] Never describe this prototype as an official PM-AJAY enrollment, placement, or application system.

## 3. Must-have features

| ID | Feature | Implementation guidance | Acceptance check |
|---|---|---|---|
| F01 | Mobile-first accessible interface | Build with React, TypeScript, Vite, and Tailwind or plain CSS. Use readable text, large tap targets, keyboard support, clear progress, and minimal page weight. | User can finish the journey on a narrow phone screen without voice. |
| F02 | Hindi and English guidance | Provide a language switch and short, empathetic prompts. Store the selected language for the session. Avoid claims of automatic dialect detection until tested. | Switching language preserves progress and the user understands the next step. |
| F03 | Text chat with optional speech input | Keep a text field visible. Add browser `SpeechRecognition` only when supported; request microphone permission when the user taps the control. Let users edit the transcript. | Denied microphone access or an unsupported browser does not block completion. |
| F04 | Optional spoken responses | Use browser `speechSynthesis` with available voices; provide mute, stop, and replay controls. Keep every response visible in text. | User can stop playback and read the full reply. |
| F05 | Consent and transparent disclosure | Explain that AI may be inaccurate, what information is processed, what is saved, and how to delete it. Offer a guest path. | Nothing personal is persisted without the user's explicit choice. |
| F06 | Multi-turn beneficiary profile | Track district, education, current livelihood, existing skills, interests, mobility, accessibility needs, and employment preference in a typed JSON object. Allow `unknown`. Start with guided questions; optionally add server-side AI extraction with schema validation. | Multiple facts from one answer are captured, retained across turns, and reviewable. |
| F07 | Profile review and correction | Show a concise summary before matching. Mark fields as confirmed, inferred, or unknown. Use only confirmed answers for strict eligibility or travel filters. | Editing education or mobility updates the displayed recommendations. |
| F08 | Verified NSQF qualification catalog | Curate a small JSON/CSV dataset from official NQR pages: identifier, title, level, eligibility text if published, source link, and verification date. | Each suggested qualification links to its exact official record. |
| F09 | Local opportunity evidence | Maintain opportunities separately from qualifications: district, provider if verified, status, source, and last checked date. Treat a district skill plan as context, not proof of active seats. | If local availability is unverified, the page says so explicitly. |
| F10 | Explainable matching and skill gaps | Filter by confirmed constraints; rank remaining qualifications by interests and existing skills. Show why each appears, what skills are missing, and a next step. Do not let AI invent records or bypass filters. | Results include reasons, criteria, evidence, and location caveats. |
| F11 | Scheme and counselor guidance | Link to official PM-AJAY and NQR information; show an option to seek help from a human counselor. Separate possible pathways from actual eligibility or approval. | No response promises a grant, enrollment, placement, or official endorsement. |
| F12 | Save, resume, and print | Let users optionally keep a session locally and clear it. Add an authenticated database only if cross-device access is needed. Use browser print for a readable summary. Avoid retaining audio recordings. | User can resume, delete the stored session, and print a summary. |
| F13 | Assisted-use flow | Add a visible “helping someone else” mode for counselors, with the same consent and correction steps. | A helper can finish a session without implying government authorization. |
| F14 | Errors and fallback paths | Handle slow connections, unanswered questions, AI unavailability, speech failure, and no verified matches. Keep guided questions and deterministic matching operational. | The core journey works with both AI and microphone disabled. |
| F15 | Privacy and security | Keep secrets server-side; validate inputs; limit request size; avoid sensitive information in logs; apply row-level security to any exposed profile tables. | No secret is shipped to the browser; users cannot access each other's saved data. |
| F16 | Testing and fairness | Test Hindi, English, mixed-language input, corrections, mobility limits, unclear answers, browser compatibility, and stereotyped recommendations. Track aggregate completion and drop-off without identifying users. | Issues are documented and checked before demonstration. |

## 4. Later-phase capabilities

These ideas appear in the project blueprint but are **not prerequisites for the initial web prototype**:

- Feature-phone IVR and a dedicated telephone number.
- Automated WhatsApp voice-note conversations.
- Real-time streaming audio, interruption handling, and strict response-latency targets.
- Broad dialect coverage, accent-specific model adaptation, and advanced neural voices.
- Nationwide NQR and district-plan ingestion with vector search.
- Live government application, beneficiary-ID, enrollment, and placement integrations.

Do not represent these capabilities as implemented until the required infrastructure, permissions, datasets, and validation exist. A web-based IVR simulation may be used for demonstrations if clearly labeled as a simulation.

## 5. Suggested implementation stack

| Layer | Recommended approach | Design note |
|---|---|---|
| Frontend | React + TypeScript + Vite with Tailwind or plain CSS | Build a responsive web interface first. |
| Hosting | Static web deployment on a suitable developer hosting service | Check the selected service's current usage rules and project eligibility before release. |
| Catalog | Version-controlled `qualifications.json` and `opportunities.json` | Keep datasets small, reviewed, and source-linked. |
| Persistent profiles | Browser storage with clear user choice; Supabase only if account-based sync becomes necessary | Apply authentication and row-level security to personal records. |
| AI assistance | Optional server-side Gemini text model for structured extraction and empathetic phrasing | Validate structured output; limit requests; preserve a guided-question fallback. |
| Speech input/output | Browser Web Speech API, where available | Text must remain the reliable baseline. |
| Matching | TypeScript rules over the curated catalog | Hard constraints first, transparent ranking second. |
| Summary | Browser print view | Avoid storing or uploading voice recordings by default. |

Keep API secrets outside client code. If a selected service cannot be used within the project's deployment constraints, disable that optional integration rather than blocking the core experience. Browser recognition behavior can vary by device and may involve a remote recognition service, so disclose processing accurately.

## 6. Suggested data shapes

```ts
type Profile = {
  sessionId: string;
  consentToSave: boolean;
  language: 'hi' | 'en';
  district?: string;
  education?: string;
  currentWork?: string;
  skills: string[];
  interests: string[];
  mobility?: 'local_only' | 'district' | 'flexible' | 'unknown';
  accessNeeds?: string[];
  employmentPreference?: 'wage' | 'self_employment' | 'either' | 'unknown';
  confirmedFields: string[];
  updatedAt: string;
};

type Qualification = {
  id: string;
  title: string;
  nsqfLevel?: string;
  eligibilityText?: string;
  skillTags: string[];
  officialUrl: string;
  lastVerifiedAt: string;
};

type Opportunity = {
  qualificationId: string;
  district: string;
  provider?: string;
  availability: 'verified_open' | 'unknown' | 'closed';
  sourceUrl: string;
  lastVerifiedAt: string;
};
```

Use real identifiers from verified qualification records. Keep opportunity availability independent from qualification existence. For account-based profiles, restrict each record to its owner; a guest session does not need a database row.

## 7. Development order

1. **Curate sources:** Review 10–20 NQR qualification records and collect eligibility details, direct links, and verification dates. Add local opportunities only when separately verified.
2. **Build the complete text journey:** Create language choice, disclosure, guided chat, profile review, matching results, correction, and print view.
3. **Implement deterministic matching:** Validate profile fields, enforce hard constraints, rank by skill/interest overlap, and show evidence with every result.
4. **Add optional voice:** Detect browser support, make transcripts editable, and provide playback controls. Test the entire experience without speech features.
5. **Add optional AI assistance:** Extract structured answers on the server, validate output, prevent invented qualifications, and handle service unavailability.
6. **Add persistence if necessary:** Implement local save/delete first; add accounts and protected database records only when the use case requires them.
7. **Test with realistic scenarios:** Check accessibility, low connectivity, mixed language, source freshness, privacy, stereotype risks, and no-result states.

**Definition of done:** A user can complete the full text-based journey; every displayed qualification has a genuine source; local availability is never assumed; errors do not prevent completion; consent, correction, deletion, and scheme caveats work.

## 8. Supporting references

- Background document: `PM-AJAY-AI-Voice-Assistant.pdf`.
- [PM-AJAY official portal](https://pmajay.dosje.gov.in/) and [scheme guidelines](https://pmajay.dosje.gov.in/Writereaddata/Guidelines.pdf).
- [National Qualifications Register](https://www.nqr.gov.in/qualifications-search).
- [Supabase row-level security guide](https://supabase.com/docs/guides/database/postgres/row-level-security).
- [MDN Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) and [SpeechRecognition compatibility notes](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).
