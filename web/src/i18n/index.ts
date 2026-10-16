import { watch } from 'vue'
import { createI18n } from 'vue-i18n'
import en from './en'
import he from './he'

export type Locale = 'en' | 'he'

const STORAGE_KEY = 'meshmind.locale'

function savedLocale(): Locale {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'he' ? 'he' : 'en'
  } catch {
    return 'en'
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: savedLocale(),
  fallbackLocale: 'en',
  messages: { en, he },
})

export const currentLocale = () => i18n.global.locale.value as Locale

/** Intl locale used for numbers: Israeli formatting in Hebrew, British in English. */
export const intlLocale = () => (currentLocale() === 'he' ? 'he-IL' : 'en-GB')

function applyDocumentLanguage(locale: Locale) {
  document.documentElement.lang = locale
  document.documentElement.dir = locale === 'he' ? 'rtl' : 'ltr'
}

applyDocumentLanguage(currentLocale())
watch(i18n.global.locale, (locale) => {
  applyDocumentLanguage(locale as Locale)
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // Without storage the choice simply lasts for this visit.
  }
})

export function toggleLocale() {
  i18n.global.locale.value = currentLocale() === 'he' ? 'en' : 'he'
}
