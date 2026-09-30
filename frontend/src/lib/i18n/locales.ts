export type SupportedLocale =
  | "en"
  | "hi"
  | "bn"
  | "mr"
  | "ta";

export type LocaleCapability = {
  code: SupportedLocale;
  label: string;
  nativeLabel: string;
  short: string;
  direction: "ltr" | "rtl";
  uiSupported: boolean;
  aiSupported: boolean;
  sttSupported: boolean;
  ttsSupported: boolean;
  enabled: boolean;
};

export const DEFAULT_LOCALE: SupportedLocale = "en";

export const LOCALES: Record<SupportedLocale, LocaleCapability> = {
  en: {
    code: "en",
    label: "English",
    nativeLabel: "English",
    short: "EN",
    direction: "ltr",
    uiSupported: true,
    aiSupported: true,
    sttSupported: true,
    ttsSupported: true,
    enabled: true,
  },
  hi: {
    code: "hi",
    label: "Hindi",
    nativeLabel: "हिन्दी",
    short: "हि",
    direction: "ltr",
    uiSupported: true,
    aiSupported: true,
    sttSupported: true,
    ttsSupported: true,
    enabled: true,
  },
  bn: {
    code: "bn",
    label: "Bengali",
    nativeLabel: "বাংলা",
    short: "বা",
    direction: "ltr",
    uiSupported: false,
    aiSupported: false,
    sttSupported: false,
    ttsSupported: false,
    enabled: false,
  },
  mr: {
    code: "mr",
    label: "Marathi",
    nativeLabel: "मराठी",
    short: "म",
    direction: "ltr",
    uiSupported: false,
    aiSupported: false,
    sttSupported: false,
    ttsSupported: false,
    enabled: false,
  },
  ta: {
    code: "ta",
    label: "Tamil",
    nativeLabel: "தமிழ்",
    short: "த",
    direction: "ltr",
    uiSupported: false,
    aiSupported: false,
    sttSupported: false,
    ttsSupported: false,
    enabled: false,
  },
};

export function getEnabledLocales(): LocaleCapability[] {
  return Object.values(LOCALES).filter((loc) => loc.enabled);
}

export function isSupportedLocale(code: string): code is SupportedLocale {
  return Object.prototype.hasOwnProperty.call(LOCALES, code);
}

export function isLocaleEnabled(code: string): boolean {
  return isSupportedLocale(code) && LOCALES[code].enabled;
}

export function getLocaleCapability(code: string): LocaleCapability {
  if (isSupportedLocale(code)) {
    return LOCALES[code];
  }
  return LOCALES[DEFAULT_LOCALE];
}
