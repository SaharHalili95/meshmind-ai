import { intlLocale } from '@/i18n'

export const fmt = (value: number, digits = 2) =>
  new Intl.NumberFormat(intlLocale(), { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)

export const pct = (value: number, digits = 1) =>
  new Intl.NumberFormat(intlLocale(), { style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
