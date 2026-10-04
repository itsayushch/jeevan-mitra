# JeevanMitra 2.0 Accessibility (a11y) & Localization QA Plan

## 1. Compliance Target

JeevanMitra 2.0 is designed to adhere to **WCAG 2.1 Level AA** standards and the **Guidelines for Indian Government Websites (GIGW 3.0)** to ensure equitable access for rural and semi-urban citizens with varied physical and digital capabilities.

---

## 2. Core Accessibility Controls

| Area | Requirement | Implementation in JeevanMitra |
| :--- | :--- | :--- |
| **Keyboard Navigation** | Full keyboard operability (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Esc`). | Visible focus rings (`focus:ring-2 focus:ring-emerald-500`); skip-links to main content. |
| **Screen Reader Support** | Clean reading order, semantic HTML, and descriptive ARIA landmarks. | `aria-live="polite"` on chat messages, `aria-expanded` on accordions, `role="status"` on notifications. |
| **Color Contrast** | Minimum 4.5:1 for normal body text; 3:0 for large headings and icons. | Neutral slate background with high-contrast text (`text-slate-900` on white, `text-emerald-800` on emerald badges). |
| **Touch Targets** | Minimum $48 \times 48$ px for buttons and interactive controls. | Tailwind `min-h-[44px] min-w-[44px] p-3` applied across mobile touchpoints. |
| **Typography & Scaling**| 200% zoom support without horizontal scrolling or text clipping. | Relative `rem` units, fluid responsive layouts. |

---

## 3. Bilingual Localization & Typography QA

### Supported vs Disabled Languages Guardrail
- **Active & Supported**: English (`en`) and Hindi (`hi`).
- **Disabled Until Verified**: Bengali (`bn`), Marathi (`mr`), Tamil (`ta`).
- **Policy**: A language is never displayed in the picker unless UI translations, backend validation, AI generation, and speech tools are verified end-to-end.

### Localization QA Checklist

| Check | Hindi (`hi`) | English (`en`) | Status |
| :--- | :--- | :--- | :--- |
| **Devanagari Font Rendering** | Clean rendering using Noto Sans Devanagari | Inter font family | **PASSED** |
| **Translation Key Parity** | 100% key parity with English master dictionary | Master template | **PASSED** (Validated in `test_locale_parity.py`) |
| **Date & Currency Format** | `DD/MM/YYYY`, `₹` (INR symbol) | `DD/MM/YYYY`, `₹` (INR symbol) | **PASSED** |
| **Dynamic Interpolation** | Grammatically correct placeholder substitution | Standard templating | **PASSED** |
| **Text Truncation Check** | No overflow or clipping in button labels or table headers | Verified | **PASSED** |

---

## 4. Multimodal Accessibility (Voice & Audio)

1. **Speech-to-Text (STT) Graceful Degradation**:
   - When microphone access is denied or unavailable, the UI seamlessly falls back to typed input without error modals.
2. **Audio Explanations**:
   - Recommendation audio explanations (`audio_explanation_script`) are always paired with visible on-screen text transcripts for hard-of-hearing beneficiaries.
3. **Low-Bandwidth Resilience**:
   - Voice assistant uses lightweight audio compression; Next.js static pages load in $< 130$ KB first-load JS.
