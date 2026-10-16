<script setup lang="ts">
import Accordion from 'primevue/accordion'
import AccordionContent from 'primevue/accordioncontent'
import AccordionHeader from 'primevue/accordionheader'
import AccordionPanel from 'primevue/accordionpanel'
import Checkbox from 'primevue/checkbox'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { pick } from '@/content/localized'
import { issues, type IssueCategory } from '@/content/troubleshooting'
import type { Locale } from '@/i18n'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as Locale)

const categories: IssueCategory[] = ['setup', 'quality', 'learning', 'experiments']
const categoryOptions = computed(() => categories.map((value) => ({ value, label: t(`troubleshooting.categories.${value}`) })))

const search = ref('')
const category = ref<IssueCategory | null>(null)
const onlyReal = ref(false)

const visible = computed(() => {
  const term = search.value.trim().toLowerCase()
  return issues.filter((issue) => {
    if (category.value && issue.category !== category.value) return false
    if (onlyReal.value && !issue.real) return false
    if (!term) return true
    // Search both languages so an English error message pasted into the Hebrew UI still matches.
    const haystack = [issue.title, issue.symptom, issue.cause, ...issue.fix, ...(issue.lesson ? [issue.lesson] : [])]
      .flatMap((text) => [text.en, text.he])
      .join(' ')
      .toLowerCase()
    return haystack.includes(term)
  })
})

/** Renders `inline code` spans inside plain text without v-html. */
const parts = (text: string) => text.split(/(`[^`]+`)/).filter(Boolean).map((p) => ({ code: p.startsWith('`'), text: p.replace(/`/g, '') }))
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ t('troubleshooting.title') }}</h1>
        <p>{{ t('troubleshooting.subtitle') }}</p>
      </div>
    </div>

    <section class="panel">
      <div class="toolbar">
        <IconField>
          <InputIcon class="pi pi-search" />
          <InputText v-model="search" :placeholder="t('troubleshooting.search')" :aria-label="t('troubleshooting.search')" />
        </IconField>
        <Select v-model="category" :options="categoryOptions" option-label="label" option-value="value"
          :placeholder="t('troubleshooting.allCategories')" show-clear :aria-label="t('troubleshooting.allCategories')" />
        <label class="real-filter">
          <Checkbox v-model="onlyReal" binary input-id="only-real" />
          <span>{{ t('troubleshooting.onlyReal') }}</span>
        </label>
        <span class="muted count">{{ t('troubleshooting.count', { count: visible.length }) }}</span>
      </div>

      <p v-if="visible.length === 0" class="muted">{{ t('troubleshooting.empty') }}</p>

      <Accordion v-else multiple>
        <AccordionPanel v-for="issue in visible" :key="issue.id" :value="issue.id">
          <AccordionHeader>
            <span class="issue-head">
              <span class="issue-title"><span class="muted num">#{{ issue.id }}</span> {{ pick(issue.title, lang) }}</span>
              <span class="issue-tags">
                <Tag v-if="issue.real" icon="pi pi-bolt" :value="t('troubleshooting.real')" severity="warn" />
                <Tag :value="t(`troubleshooting.categories.${issue.category}`)" severity="secondary" />
              </span>
            </span>
          </AccordionHeader>
          <AccordionContent>
            <dl class="issue-body">
              <dt>{{ t('troubleshooting.symptom') }}</dt>
              <dd><template v-for="(p, i) in parts(pick(issue.symptom, lang))" :key="i"><code v-if="p.code">{{ p.text }}</code><span v-else>{{ p.text }}</span></template></dd>
              <dt>{{ t('troubleshooting.cause') }}</dt>
              <dd><template v-for="(p, i) in parts(pick(issue.cause, lang))" :key="i"><code v-if="p.code">{{ p.text }}</code><span v-else>{{ p.text }}</span></template></dd>
              <dt>{{ t('troubleshooting.fix') }}</dt>
              <dd>
                <ol>
                  <li v-for="(step, i) in issue.fix" :key="i">
                    <template v-for="(p, j) in parts(pick(step, lang))" :key="j"><code v-if="p.code">{{ p.text }}</code><span v-else>{{ p.text }}</span></template>
                  </li>
                </ol>
              </dd>
              <template v-if="issue.lesson">
                <dt>{{ t('troubleshooting.lesson') }}</dt>
                <dd class="lesson">{{ pick(issue.lesson, lang) }}</dd>
              </template>
              <template v-if="issue.code">
                <dt>{{ t('troubleshooting.code') }}</dt>
                <dd><a :href="`https://github.com/SaharHalili95/meshmind-ai/blob/main/${issue.code}`" target="_blank" rel="noopener"><code>{{ issue.code }}</code></a></dd>
              </template>
            </dl>
          </AccordionContent>
        </AccordionPanel>
      </Accordion>
    </section>
  </div>
</template>

<style scoped>
.count { margin-inline-start: auto; }
.real-filter { display: inline-flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.issue-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; width: 100%; flex-wrap: wrap; }
.issue-title { font-weight: 600; text-align: start; }
.issue-tags { display: flex; gap: 0.375rem; margin-inline-end: 0.5rem; }
.issue-body { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 0.5rem 1.25rem; line-height: 1.6; }
.issue-body dt { font-weight: 600; color: var(--app-text-muted); }
.issue-body dd { margin: 0; }
.issue-body ol { margin: 0; padding-inline-start: 1.25rem; }
.issue-body code { font-size: 0.8125rem; word-break: break-word; }
.issue-body a { color: var(--app-accent); }
.lesson { font-weight: 550; }
@media (max-width: 640px) {
  .issue-body { grid-template-columns: 1fr; }
  .issue-body dt { margin-top: 0.5rem; }
}
</style>
