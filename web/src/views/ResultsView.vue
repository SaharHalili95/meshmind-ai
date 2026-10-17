<script setup lang="ts">
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import Tag from 'primevue/tag'
import type { ChartConfiguration } from 'chart.js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import ChartCanvas, { type ChartTokens } from '@/components/ChartCanvas.vue'
import StatTile from '@/components/StatTile.vue'
import { results, type MetricKey } from '@/data/results'
import { POLICY_ORDER, type PolicyName } from '@/sim/policies'
import { fmt, pct } from '@/utils/format'

const { t, locale } = useI18n()
const router = useRouter()

const p = results.policies
const seeds = results.seeds
const rows = (policy: PolicyName) => results.perSeed.filter((r) => r.policy === policy)
const pdrGaps = seeds.map((seed) => {
  const ql = results.perSeed.find((r) => r.seed === seed && r.policy === 'q_learning')!
  const sp = results.perSeed.find((r) => r.seed === seed && r.policy === 'shortest_path')!
  return ql.pdr - sp.pdr
})
const utilSaving = 1 - p.q_learning.avg_link_utilization.mean / p.congestion_aware.avg_link_utilization.mean
const heldOutFlows = seeds.length * results.config.eval_episodes * results.config.traffic.flows_per_episode

const comparisons = results.comparisons.filter((c) => c.baseline !== 'random')
const vsShortest = results.comparisons.find((c) => c.baseline === 'shortest_path' && c.metric === 'pdr')!
const scaleOf = (c: { metric: MetricKey }) => (c.metric === 'mean_latency_ms' ? 1 : 100)
const unitOf = (c: { metric: MetricKey }) => (c.metric === 'mean_latency_ms' ? ' ms' : ` ${t('results.pts')}`)
const signed = (v: number, digits = 2) => `${v > 0 ? '+' : ''}${fmt(v, digits)}`
const pValue = (v: number) => (v < 0.001 ? '< 0.001' : fmt(v, 3))

const metricOptions = computed(() =>
  (['pdr', 'mean_latency_ms', 'mean_throughput', 'avg_link_utilization'] as MetricKey[]).map((value) => ({ value, label: t(`metrics.${value}`) })))
const metric = ref<MetricKey>('pdr')

const digits: Record<MetricKey, number> = { pdr: 3, plr: 3, mean_latency_ms: 1, mean_throughput: 1, avg_link_utilization: 3, routing_failures: 0, mean_hops: 2 }
const cell = (policy: PolicyName, key: MetricKey) => `${fmt(p[policy][key].mean, digits[key])} ± ${fmt(p[policy][key].std, digits[key])}`

const comparisonChart = computed(() => {
  const key = metric.value
  void locale.value
  return (tk: ChartTokens): ChartConfiguration => ({
    type: 'bar',
    data: {
      labels: POLICY_ORDER.map((name) => t(`policies.${name}`)),
      datasets: [{
        label: t(`metrics.${key}`),
        data: POLICY_ORDER.map((name) => p[name][key].mean),
        backgroundColor: tk.series,
        borderColor: tk.surface,
        borderWidth: 2,
        borderRadius: 4,
        maxBarThickness: 64,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `${t(`metrics.${key}`)}: ${cell(POLICY_ORDER[ctx.dataIndex]!, key)}` } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tk.text } },
        y: { beginAtZero: true, grid: { color: tk.grid }, ticks: { color: tk.text } },
      },
    },
  })
})

const sweepChart = computed(() => {
  void locale.value
  const sweep = results.loadSweep
  const labels = sweep.map((pt) => fmt(pt.relative_load, 2))
  return (tk: ChartTokens): ChartConfiguration => {
    const lines = (['shortest_path', 'congestion_aware'] as const).flatMap((baseline, i) => {
      const color = tk.series[i + 1]!
      const name = t('results.sig.vs', { name: t(`policies.${baseline}`) })
      return [
        { label: `${name} high`, data: sweep.map((pt) => pt[baseline].ci_high * 100), borderWidth: 0, pointRadius: 0, fill: '+2', backgroundColor: `${color}26` },
        {
          label: name,
          data: sweep.map((pt) => pt[baseline].mean_diff * 100),
          borderColor: color,
          borderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          pointBorderWidth: 2,
          pointBorderColor: color,
          pointBackgroundColor: sweep.map((pt) => (pt[baseline].significant ? color : tk.surface)),
          fill: false,
        },
        { label: `${name} low`, data: sweep.map((pt) => pt[baseline].ci_low * 100), borderWidth: 0, pointRadius: 0, fill: false },
      ]
    })
    return {
      type: 'line',
      data: { labels, datasets: lines },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: tk.text, usePointStyle: true, filter: (item) => !/ (high|low)$/.test(item.text) } },
          tooltip: {
            filter: (item) => item.datasetIndex % 3 === 1,
            callbacks: {
              title: (items) => `${t('results.sweepX')}: ${items[0]?.label}`,
              label: (ctx) => {
                const baseline = ctx.datasetIndex < 3 ? 'shortest_path' : 'congestion_aware'
                const c = sweep[ctx.dataIndex]![baseline]
                return `${ctx.dataset.label}: ${signed(c.mean_diff * 100)} ${t('results.pts')} (p ${pValue(c.p_value)})`
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: tk.text }, title: { display: true, text: t('results.sweepX'), color: tk.text } },
          y: { grid: { color: (ctx) => (ctx.tick.value === 0 ? tk.text : tk.grid) }, ticks: { color: tk.text }, title: { display: true, text: t('results.sweepY'), color: tk.text } },
        },
      },
    }
  }
})

const rewardChart = computed(() => {
  void locale.value
  const c = results.rewardCurve
  return (tk: ChartTokens): ChartConfiguration => ({
    type: 'line',
    data: {
      labels: c.episode,
      datasets: [
        { label: '+1 std', data: c.mean.map((m, i) => m + c.std[i]!), borderWidth: 0, pointRadius: 0, fill: '+1', backgroundColor: `${tk.series[0]}2e` },
        { label: t('results.rewardMean'), data: c.mean, borderColor: tk.series[0], borderWidth: 2, pointRadius: 0, fill: false },
        { label: '-1 std', data: c.mean.map((m, i) => m - c.std[i]!), borderWidth: 0, pointRadius: 0, fill: false },
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          filter: (item) => item.datasetIndex === 1,
          callbacks: { title: (items) => `${t('results.episode')} ${items[0]?.label}` },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tk.text, maxTicksLimit: 7 }, title: { display: true, text: t('results.episode'), color: tk.text } },
        y: { grid: { color: tk.grid }, ticks: { color: tk.text }, title: { display: true, text: t('results.reward'), color: tk.text } },
      },
    },
  })
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ t('results.title') }}</h1>
        <p>{{ t('results.subtitle') }}</p>
      </div>
    </div>

    <section class="panel hero">
      <div>
        <div class="eyebrow">{{ t('results.questionLabel') }}</div>
        <h2 class="question">{{ t('results.question') }}</h2>
        <p class="muted">{{ t('results.answer') }}</p>
      </div>
      <div class="cta">
        <Button :label="t('results.trySimulator')" icon="pi pi-play" @click="router.push('/simulator')" />
        <Button :label="t('results.howItWorks')" icon="pi pi-share-alt" severity="secondary" outlined @click="router.push('/architecture')" />
      </div>
    </section>

    <div class="tiles">
      <StatTile icon="pi pi-send" :label="t('results.tilePdr')" :value="pct(p.q_learning.pdr.mean)"
        :caption="t('results.tilePdrCaption', { std: fmt(p.q_learning.pdr.std * 100, 1), seeds: seeds.length })" />
      <StatTile icon="pi pi-arrow-up-right" :label="t('results.tileGain')" :value="`${signed(vsShortest.mean_diff * 100)} ${t('results.pts')}`"
        :caption="t('results.tileGainCaption', { low: signed(vsShortest.ci_low * 100), high: signed(vsShortest.ci_high * 100), p: pValue(vsShortest.p_value), wins: vsShortest.wins, n: vsShortest.n })" />
      <StatTile icon="pi pi-bolt" :label="t('results.tileUtil')" :value="pct(utilSaving)" :caption="t('results.tileUtilCaption')" />
      <StatTile icon="pi pi-check-circle" :label="t('results.tileFailures')" :value="fmt(p.q_learning.routing_failures.mean, 0)" :caption="t('results.tileFailuresCaption', { flows: heldOutFlows.toLocaleString() })" />
    </div>

    <div class="grid-2">
      <section class="panel">
        <h2>{{ t('results.comparison') }}</h2>
        <div class="panel-head">
          <SelectButton v-model="metric" :options="metricOptions" option-label="label" option-value="value" :allow-empty="false" size="small" />
        </div>
        <ChartCanvas :build="comparisonChart" :label="t('results.comparison')" :height="300" />
        <p class="muted note">{{ t(`results.metricNote.${metric}`) }}</p>
      </section>
      <section class="panel">
        <h2>{{ t('results.rewardTitle') }}</h2>
        <ChartCanvas :build="rewardChart" :label="t('results.rewardTitle')" :height="300" />
        <p class="muted note">{{ t('results.rewardNote', { window: results.rewardCurve.window, seeds: seeds.length }) }}</p>
      </section>
    </div>

    <section class="panel table-panel">
      <h2>{{ t('results.tableTitle') }}</h2>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('results.policy') }}</th>
              <th v-for="key in ['pdr', 'plr', 'mean_latency_ms', 'mean_throughput', 'avg_link_utilization', 'routing_failures']" :key="key">
                {{ t(`metrics.${key}`) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="name in POLICY_ORDER" :key="name" :class="{ highlight: name === 'q_learning' }">
              <td><span class="swatch" :class="name" />{{ t(`policies.${name}`) }}</td>
              <td v-for="key in (['pdr', 'plr', 'mean_latency_ms', 'mean_throughput', 'avg_link_utilization', 'routing_failures'] as MetricKey[])" :key="key" class="num">
                {{ cell(name, key) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted note">{{ t('results.tableNote', { flows: (results.config.eval_episodes * results.config.traffic.flows_per_episode).toLocaleString(), seeds: seeds.length }) }}</p>
    </section>

    <section class="panel sig-panel">
      <h2>{{ t('results.sigTitle') }}</h2>
      <p class="muted note top">{{ t('results.sigIntro', { n: seeds.length }) }}</p>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('results.sig.comparison') }}</th>
              <th>{{ t('results.sig.diff') }}</th>
              <th>{{ t('results.sig.ci') }}</th>
              <th>{{ t('results.sig.p') }}</th>
              <th>{{ t('results.sig.wins') }}</th>
              <th>{{ t('results.sig.verdict') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in comparisons" :key="`${c.baseline}-${c.metric}`">
              <td>{{ t(`metrics.${c.metric}`) }} · {{ t('results.sig.vs', { name: t(`policies.${c.baseline}`) }) }}</td>
              <td class="num">{{ signed(c.mean_diff * scaleOf(c)) }}{{ unitOf(c) }}</td>
              <td class="num">[{{ signed(c.ci_low * scaleOf(c)) }}, {{ signed(c.ci_high * scaleOf(c)) }}]</td>
              <td class="num">{{ pValue(c.p_value) }}</td>
              <td class="num">{{ c.wins }}/{{ c.n }}</td>
              <td>
                <Tag v-if="c.significant" icon="pi pi-check" :value="t('results.sig.significant')" severity="success" />
                <Tag v-else icon="pi pi-minus" :value="t('results.sig.notSignificant')" severity="secondary" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted note">{{ t('results.sigNote') }}</p>
    </section>

    <section v-if="results.loadSweep.length" class="panel sig-panel">
      <h2>{{ t('results.sweepTitle') }}</h2>
      <p class="muted note top">{{ t('results.sweepIntro') }}</p>
      <ChartCanvas :build="sweepChart" :label="t('results.sweepTitle')" :height="320" />
      <p class="muted note">{{ t('results.sweepNote', { n: seeds.length }) }}</p>
    </section>

    <div class="grid-2">
      <section class="panel">
        <h2>{{ t('results.pairedTitle') }}</h2>
        <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Seed</th>
              <th v-for="name in POLICY_ORDER.slice(0, 3)" :key="name">{{ t(`policies.${name}`) }}</th>
              <th>{{ t('results.gap') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(seed, i) in seeds" :key="seed">
              <td class="num">{{ seed }}</td>
              <td v-for="name in POLICY_ORDER.slice(0, 3)" :key="name" class="num">{{ fmt(rows(name)[i]!.pdr, 4) }}</td>
              <td class="num gain">{{ signed(pdrGaps[i]! * 100) }}</td>
            </tr>
          </tbody>
        </table>
        </div>
        <p class="muted note">{{ t('results.pairedNote') }}</p>
      </section>
      <section class="panel">
        <h2>{{ t('results.setupTitle') }}</h2>
        <dl class="setup">
          <dt>{{ t('results.setup.topology') }}</dt><dd>{{ t('results.setup.topologyValue') }}</dd>
          <dt>{{ t('results.setup.traffic') }}</dt><dd>{{ t('results.setup.trafficValue') }}</dd>
          <dt>{{ t('results.setup.training') }}</dt><dd>{{ t('results.setup.trainingValue', { episodes: results.config.train_episodes.toLocaleString() }) }}</dd>
          <dt>{{ t('results.setup.evaluation') }}</dt><dd>{{ t('results.setup.evaluationValue', { episodes: results.config.eval_episodes }) }}</dd>
          <dt>{{ t('results.setup.seeds') }}</dt><dd class="num">{{ seeds.join(', ') }}</dd>
          <dt>{{ t('results.setup.agent') }}</dt>
          <dd class="ltr">α = {{ results.config.agent.alpha }}, γ = {{ results.config.agent.gamma }}, ε {{ results.config.agent.epsilon_start }} → {{ results.config.agent.epsilon_end }} (×{{ results.config.agent.epsilon_decay }})</dd>
        </dl>
        <p class="muted note"><i class="pi pi-info-circle" /> {{ t('results.scope') }}</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.hero { display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1rem;
  background: linear-gradient(135deg, color-mix(in srgb, var(--app-accent) 9%, var(--app-surface)), var(--app-surface)); }
.eyebrow { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--app-accent); font-weight: 650; }
.question { font-size: 1.125rem; margin: 0.375rem 0 0.5rem; max-width: 760px; line-height: 1.45; }
.hero p { margin: 0; max-width: 760px; line-height: 1.6; }
.cta { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.panel-head { margin-bottom: 1rem; }
.note { font-size: 0.8125rem; margin: 0.75rem 0 0; line-height: 1.55; }
.note.top { margin: -0.5rem 0 1rem; }
.sig-panel { margin-bottom: 1rem; }
.table-panel { margin: 1rem 0; }
.table-wrap { overflow-x: auto; }
.highlight td { font-weight: 600; }
.swatch { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-inline-end: 0.5rem; vertical-align: middle; }
.swatch.q_learning { background: var(--chart-series-1); }
.swatch.shortest_path { background: var(--chart-series-2); }
.swatch.congestion_aware { background: var(--chart-series-3); }
.swatch.random { background: var(--chart-series-4); }
.gain { font-weight: 650; }
.setup { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 0.5rem 1.25rem; margin: 0; line-height: 1.5; }
.setup dt { color: var(--app-text-muted); font-weight: 550; }
.setup dd { margin: 0; }
</style>
