<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { pick } from '@/content/localized'
import { summarySections } from '@/content/projectSummary'
import type { Locale } from '@/i18n'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as Locale)
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ t('about.title') }}</h1>
        <p>{{ t('about.subtitle') }}</p>
      </div>
    </div>

    <section class="panel links">
      <a href="https://github.com/SaharHalili95/meshmind-ai" target="_blank" rel="noopener"><i class="pi pi-github" /> {{ t('about.code') }}</a>
      <a href="https://github.com/SaharHalili95/meshmind-ai/tree/main/docs" target="_blank" rel="noopener"><i class="pi pi-file" /> {{ t('about.docs') }}</a>
      <a href="https://github.com/SaharHalili95/meshmind-ai/tree/main/docs/learning" target="_blank" rel="noopener"><i class="pi pi-graduation-cap" /> {{ t('about.learning') }}</a>
    </section>

    <div class="sections">
      <section v-for="section in summarySections" :key="section.id" class="panel">
        <h2><i :class="section.icon" /> {{ pick(section.title, lang) }} <code v-if="section.tech" class="tech">{{ section.tech }}</code></h2>
        <ul>
          <li v-for="(item, i) in section.items" :key="i">{{ pick(item, lang) }}</li>
        </ul>
      </section>
    </div>

    <section class="panel run">
      <h2><i class="pi pi-terminal" /> {{ t('about.runTitle') }}</h2>
      <div class="formula">git clone https://github.com/SaharHalili95/meshmind-ai.git
cd meshmind-ai
make install       # Python venv + dependencies
make test          # 116 tests
make experiments   # 3-seed benchmark + figures
cd web && npm install && npm run dev   # this website</div>
    </section>
  </div>
</template>

<style scoped>
.links { display: flex; gap: 1.25rem; flex-wrap: wrap; margin-bottom: 1rem; }
.links a { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--app-accent); text-decoration: none; font-weight: 600; }
.sections { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1rem; }
.sections h2 { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.sections h2 i, .run h2 i { color: var(--app-accent); }
.tech { font-size: 0.75rem; font-weight: 500; color: var(--app-text-muted); padding: 0.125rem 0.5rem; border: 1px solid var(--app-border); border-radius: 6px; }
ul { margin: 0; padding-inline-start: 1.25rem; display: grid; gap: 0.375rem; line-height: 1.55; }
.run { margin-top: 1rem; }
.run h2 { display: flex; align-items: center; gap: 0.5rem; }
</style>
