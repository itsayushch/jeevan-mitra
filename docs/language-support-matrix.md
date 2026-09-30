# Language Support Matrix

This matrix establishes the verified capability status for all candidate locales in JeevanMitra.
In accordance with the project verification rules, a language is marked as **Supported** and enabled in the user interface only when all system layers (UI strings, persistence, backend validation, AI generation, and speech capability/fallback) are verified.

| Language | Locale code | UI strings | Backend validation | AI generation | STT | TTS | Status shown to user |
|---|---|---:|---:|---:|---:|---:|---|
| English | en | Yes | Yes | Yes | Yes | Yes | Supported |
| Hindi | hi | Yes | Yes | Yes | Yes | Yes | Supported |
| Bengali | bn | In progress | Yes | Fallback to en/hi | Browser fallback | Browser fallback | Do not display until verified |
| Marathi | mr | In progress | Yes | Fallback to en/hi | Browser fallback | Browser fallback | Do not display until verified |
| Tamil | ta | In progress | Yes | Fallback to en/hi | Browser fallback | Browser fallback | Do not display until verified |

## Capability Definitions & Rules
1. **UI strings**: Full canonical key parity with English source dictionary. No missing keys or raw fallback keys displayed.
2. **Backend validation**: Validated against `SupportedLocale` enum and checked against enabled registry. Invalid or disabled locales degrade safely.
3. **AI generation**: Deterministic templates and guarded LLM outputs explicitly respect `response_locale`. If unsupported, clear safe fallback without false claims.
4. **STT (Speech-to-Text)**: Explicit capability declared. If unsupported for a locale, microphone input is disabled with a clear user explanation while preserving text input.
5. **TTS (Text-to-Speech)**: Explicit capability declared. If unsupported for a locale, audio playback button is disabled with an explanation while text content is rendered.
6. **Active Enablement**: Only `en` and `hi` are `enabled: true`. Locales `bn`, `mr`, and `ta` are configured in the registry but disabled from selection until verified end-to-end.
