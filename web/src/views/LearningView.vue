<script setup lang="ts">
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { concepts, decisions, exercises, phases, quiz } from '@/content/learning'
import { pick } from '@/content/localized'
import type { Locale } from '@/i18n'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as Locale)
const tab = ref('concepts')
const revealed = ref(new Set<number>())
function toggle(i: number) {
  const next = new Set(revealed.value)
  if (next.has(i)) next.delete(i)
  else next.add(i)
  revealed.value = next
}
const levelSeverity = { 1: 'success', 2: 'info', 3: 'warn', 4: 'danger' } as const
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ t('learning.title') }}</h1>
        <p>{{ t('learning.subtitle') }}</p>
      </div>
    </div>

    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="concepts"><i class="pi pi-lightbulb" /> {{ t('learning.tabs.concepts') }}</Tab>
        <Tab value="plan"><i class="pi pi-calendar" /> {{ t('learning.tabs.plan') }}</Tab>
        <Tab value="decisions"><i class="pi pi-sitemap" /> {{ t('learning.tabs.decisions') }}</Tab>
        <Tab value="quiz"><i class="pi pi-question-circle" /> {{ t('learning.tabs.quiz') }}</Tab>
        <Tab value="exercises"><i class="pi pi-code" /> {{ t('learning.tabs.exercises') }}</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="concepts">
          <div class="cards">
            <article v-for="c in concepts" :key="c.term" class="card">
              <h3 class="ltr-title">{{ c.term }}</h3>
              <p>{{ pick(c.text, lang) }}</p>
              <code>{{ c.code }}</code>
            </article>
          </div>
          <div class="formula">target   = r + γ · max Q(s′,a′)        (0 when the flow ended)
TD error = target − Q(s,a)
Q(s,a)   ← Q(s,a) + α · TD error         α = 0.1, γ = 0.95</div>
        </TabPanel>

        <TabPanel value="plan">
          <p class="muted intro">{{ t('learning.planIntro') }}</p>
          <ol class="timeline">
            <li v-for="(phase, i) in phases" :key="i" :class="{ critical: phase.critical }">
              <span class="dot">{{ i + 1 }}</span>
              <div class="phase">
                <h3>{{ pick(phase.title, lang) }}</h3>
                <div class="chips"><code v-for="item in phase.items" :key="item">{{ item }}</code></div>
                <p><i class="pi pi-flag" /> <strong>{{ t('learning.checkpoint') }}:</strong> {{ pick(phase.checkpoint, lang) }}</p>
                <p v-if="phase.critical" class="critical-note"><i class="pi pi-exclamation-triangle" /> {{ pick(phase.critical, lang) }}</p>
              </div>
            </li>
          </ol>
        </TabPanel>

        <TabPanel value="decisions">
          <p class="muted intro">{{ t('learning.adrIntro') }}</p>
          <div class="cards">
            <article v-for="d in decisions" :key="d.id" class="card">
              <div class="adr-head"><Tag :value="d.id" severity="secondary" /><h3>{{ pick(d.title, lang) }}</h3></div>
              <dl>
                <dt>{{ t('learning.decision') }}</dt><dd>{{ pick(d.decision, lang) }}</dd>
                <dt>{{ t('learning.why') }}</dt><dd>{{ pick(d.why, lang) }}</dd>
                <dt>{{ t('learning.cost') }}</dt><dd>{{ pick(d.cost, lang) }}</dd>
              </dl>
            </article>
          </div>
        </TabPanel>

        <TabPanel value="quiz">
          <p class="muted intro">{{ t('learning.quizIntro') }}</p>
          <ol class="quiz">
            <li v-for="(item, i) in quiz" :key="i">
              <button type="button" class="question" :aria-expanded="revealed.has(i)" @click="toggle(i)">
                <span>{{ pick(item.q, lang) }}</span>
                <i class="pi" :class="revealed.has(i) ? 'pi-eye-slash' : 'pi-eye'" />
              </button>
              <p v-if="revealed.has(i)" class="answer">{{ pick(item.a, lang) }}</p>
            </li>
          </ol>
        </TabPanel>

        <TabPanel value="exercises">
          <p class="muted intro">{{ t('learning.exercisesIntro') }}</p>
          <div class="cards">
            <article v-for="(e, i) in exercises" :key="i" class="card">
              <div class="adr-head"><Tag :value="t('learning.level', { n: e.level })" :severity="levelSeverity[e.level]" /><h3>{{ pick(e.title, lang) }}</h3></div>
              <p>{{ pick(e.text, lang) }}</p>
            </article>
          </div>
          <p class="muted intro">
            <i class="pi pi-github" />
            <a href="https://github.com/SaharHalili95/meshmind-ai/tree/main/docs/learning" target="_blank" rel="noopener">{{ t('learning.fullGuide') }}</a>
          </p>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
.intro { margin: 0.5rem 0 1rem; line-height: 1.6; }
.intro a { color: var(--app-accent); }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin: 0.75rem 0 1rem; }
.card { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: 12px; padding: 1rem 1.125rem; display: flex; flex-direction: column; gap: 0.5rem; }
.card h3 { margin: 0; font-size: 1rem; }
.card p { margin: 0; line-height: 1.55; flex: 1; }
.card code { font-size: 0.75rem; color: var(--app-text-muted); }
.ltr-title { direction: ltr; unicode-bidi: isolate; text-align: start; }
.adr-head { display: flex; gap: 0.5rem; align-items: center; }
.card dl { margin: 0; display: grid; gap: 0.25rem; line-height: 1.5; }
.card dt { font-size: 0.75rem; font-weight: 650; color: var(--app-text-muted); margin-top: 0.25rem; }
.card dd { margin: 0; }
.timeline { list-style: none; margin: 0; padding: 0; display: grid; gap: 0; }
.timeline li { display: grid; grid-template-columns: 40px 1fr; gap: 0.75rem; position: relative; padding-bottom: 1.25rem; }
.timeline li:not(:last-child)::before { content: ''; position: absolute; inset-inline-start: 19px; top: 36px; bottom: 0; width: 2px; background: var(--app-border); }
.dot { width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; background: var(--app-accent); color: #fff; }
.critical .dot { background: var(--load-2); }
.phase { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: 12px; padding: 0.875rem 1rem; }
.phase h3 { margin: 0 0 0.5rem; font-size: 1rem; }
.phase p { margin: 0.5rem 0 0; line-height: 1.55; }
.chips { display: flex; gap: 0.375rem; flex-wrap: wrap; }
.chips code { font-size: 0.75rem; padding: 0.125rem 0.5rem; border: 1px solid var(--app-border); border-radius: 6px; }
.critical-note { color: var(--load-3); }
.quiz { margin: 0; padding-inline-start: 1.25rem; display: grid; gap: 0.75rem; }
.question { all: unset; cursor: pointer; display: flex; justify-content: space-between; gap: 1rem; width: 100%; font-weight: 600; line-height: 1.5; }
.question:focus-visible { outline: 2px solid var(--app-accent); outline-offset: 2px; border-radius: 4px; }
.answer { margin: 0.375rem 0 0; padding: 0.625rem 0.875rem; border-radius: 8px; background: color-mix(in srgb, var(--chart-series-3) 10%, transparent); line-height: 1.6; }
</style>
