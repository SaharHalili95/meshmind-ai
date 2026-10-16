import { describe, expect, it } from 'vitest'
import { flows, nodes } from '@/content/architecture'
import { concepts, decisions, exercises, phases, quiz } from '@/content/learning'
import { issues } from '@/content/troubleshooting'
import en from '@/i18n/en'
import he from '@/i18n/he'

const keys = (obj: object, prefix = ''): string[] =>
  Object.entries(obj).flatMap(([k, v]) => (typeof v === 'object' && v ? keys(v, `${prefix}${k}.`) : [`${prefix}${k}`]))

const localized = (value: unknown): { en: string; he: string }[] => {
  if (value && typeof value === 'object') {
    if ('en' in value && 'he' in value) return [value as { en: string; he: string }]
    return Object.values(value).flatMap(localized)
  }
  return []
}

describe('translations', () => {
  it('Hebrew and English catalogs have the same keys', () => {
    expect(keys(he).sort()).toEqual(keys(en).sort())
  })

  it('every long-form text exists in both languages', () => {
    const all = localized([issues, nodes, flows, concepts, phases, decisions, quiz, exercises])
    expect(all.length).toBeGreaterThan(100)
    for (const text of all) {
      expect(text.en.trim()).not.toBe('')
      expect(text.he.trim()).not.toBe('')
    }
  })
})

describe('content', () => {
  it('lists the twenty troubleshooting issues in order', () => {
    expect(issues.map((i) => i.id)).toEqual(Array.from({ length: 20 }, (_, i) => i + 1))
    expect(issues.filter((i) => i.real)).toHaveLength(7)
  })

  it('architecture flows only reference existing nodes', () => {
    const ids = new Set(nodes.map((n) => n.id))
    for (const flow of flows) for (const step of flow.steps) expect(ids.has(step.node)).toBe(true)
  })
})
