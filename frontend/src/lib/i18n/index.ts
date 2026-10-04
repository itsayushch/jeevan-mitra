import en from '../../locales/en.json';
import hi from '../../locales/hi.json';
import bn from '../../locales/bn.json';
import mr from '../../locales/mr.json';
import ta from '../../locales/ta.json';
import {
  DEFAULT_LOCALE,
  LOCALES,
  SupportedLocale,
  getEnabledLocales,
  getLocaleCapability,
  isLocaleEnabled,
  isSupportedLocale,
} from './locales';

export {
  DEFAULT_LOCALE,
  LOCALES,
  getEnabledLocales,
  getLocaleCapability,
  isLocaleEnabled,
  isSupportedLocale,
};
export type { SupportedLocale, LocaleCapability } from './locales';

export const DICTIONARIES: Record<SupportedLocale, Record<string, any>> = {
  en,
  hi,
  bn,
  mr,
  ta,
};

function getNestedValue(obj: Record<string, any>, path: string): string | undefined {
  const parts = path.split('.');
  let current: any = obj;
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = current[part];
    } else {
      return undefined;
    }
  }
  return typeof current === 'string' ? current : undefined;
}

export function translate(
  key: string,
  locale: SupportedLocale = DEFAULT_LOCALE,
  params?: Record<string, string | number>
): string {
  const activeDict = DICTIONARIES[locale] || DICTIONARIES[DEFAULT_LOCALE];
  let message = getNestedValue(activeDict, key);

  if (message === undefined && locale !== DEFAULT_LOCALE) {
    message = getNestedValue(DICTIONARIES[DEFAULT_LOCALE], key);
  }

  if (message === undefined) {
    return key;
  }

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      message = message.replace(new RegExp(`{{\\s*${k}\\s*}}`, 'g'), String(v));
    }
  }

  return message;
}
