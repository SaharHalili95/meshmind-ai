import type { Locale } from '@/i18n'

/** Long-form page content kept next to its translation instead of in the message catalogs. */
export interface Localized {
  en: string
  he: string
}

export const pick = (text: Localized, locale: Locale) => text[locale]
