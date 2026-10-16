<script setup lang="ts">
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressBar from 'primevue/progressbar'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import Slider from 'primevue/slider'
import Tag from 'primevue/tag'
import type { ChartConfiguration } from 'chart.js'
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ChartCanvas, { type ChartTokens } from '@/components/ChartCanvas.vue'
import NetworkMap, { type LinkView } from '@/components/NetworkMap.vue'
import { QLearningAgent } from '@/sim/agent'
import { NetworkEnvironment, type FlowResult, type State } from '@/sim/environment'
import {
  agentPolicy, congestionAware, evaluate, POLICY_ORDER, randomPolicy, shortestPath, summarize, trainEpisode,
  type ActionFn, type Metrics, type PolicyName,
} from '@/sim/policies'
import { NetworkTopology, TOPOLOGIES, type TopologyName } from '@/sim/topology'
import type { TrafficProfile } from '@/sim/traffic'
import { fmt, pct } from '@/utils/format'

const { t, locale } = useI18n()

const SEED = 42
const PLAYBACK_SEED = SEED + 2_000_000

/* Scenario */
const topologyName = ref<TopologyName>('abilene')
const profile = ref<TrafficProfile>('high')
const topologyOptions = computed(() => (['abilene', 'small_grid'] as TopologyName[]).map((value) => ({ value, label: t(`sim.topologies.${value}`) })))
const profileOptions = computed(() => (['low', 'moderate', 'high', 'dynamic'] as TrafficProfile[]).map((value) => ({ value, label: t(`sim.profiles.${value}`) })))
const spec = computed(() => TOPOLOGIES[topologyName.value])
const makeEnv = () => new NetworkEnvironment(new NetworkTopology(spec.value), profile.value)

/* Training */
let agent = new QLearningAgent(undefined, SEED)
let trainEnv = makeEnv()
const episodesOptions = [500, 1500, 3000]
const trainTarget = ref(3000)
const trainedEpisodes = ref(0)
const training = ref(false)
const progress = ref(0)
const curve = shallowRef<{ episode: number; reward: number }[]>([])
let rewards: number[] = []

function train() {
  if (training.value) return
  training.value = true
  stopPlayback()
  const start = trainedEpisodes.value
  const end = start + trainTarget.value
  const chunk = () => {
    if (!training.value) return
    const stop = Math.min(trainedEpisodes.value + 75, end)
    for (let e = trainedEpisodes.value; e < stop; e++) {
      rewards.push(trainEpisode(trainEnv, agent, SEED + e, e).totalReward)
      if ((e + 1) % 25 === 0) {
        const window = rewards.slice(-50)
        curve.value = [...curve.value, { episode: e + 1, reward: window.reduce((s, r) => s + r, 0) / window.length }]
      }
    }
    trainedEpisodes.value = stop
    progress.value = Math.round(((stop - start) / (end - start)) * 100)
    if (stop < end) setTimeout(chunk, 0)
    else {
      training.value = false
      comparison.value = null
      restartPlayback()
    }
  }
  setTimeout(chunk, 0)
}

const rewardChart = computed(() => {
  const data = curve.value
  void locale.value
  return (tk: ChartTokens): ChartConfiguration => ({
    type: 'line',
    data: {
      labels: data.map((d) => d.episode),
      datasets: [{ label: t('results.reward'), data: data.map((d) => d.reward), borderColor: tk.series[0], borderWidth: 2, pointRadius: 0 }],
    },
    options: {
      animation: false,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { title: (items) => `${t('results.episode')} ${items[0]?.label}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: tk.text, maxTicksLimit: 6 } },
        y: { grid: { color: tk.grid }, ticks: { color: tk.text, maxTicksLimit: 5 } },
      },
    },
  })
})

/* Playback */
const policy = ref<PolicyName>('q_learning')
const policyOptions = computed(() => POLICY_ORDER.map((value) => ({ value, label: t(`policies.${value}`) })))
let playEnv = makeEnv()
let playState: State = playEnv.reset(PLAYBACK_SEED)
let randomAct: ActionFn = randomPolicy(SEED)
const tick = ref(0)
const playing = ref(false)
const speed = ref(60)
const finished = ref<FlowResult[]>([])
const utilSamples = ref<number[]>([])
const lastFlow = ref<FlowResult | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined

const actFor = (name: PolicyName): ActionFn =>
  ({ q_learning: agentPolicy(agent), shortest_path: shortestPath, congestion_aware: congestionAware, random: randomAct })[name]

function restartPlayback() {
  stopPlayback()
  playEnv = makeEnv()
  playState = playEnv.reset(PLAYBACK_SEED)
  randomAct = randomPolicy(SEED)
  finished.value = []
  utilSamples.value = []
  lastFlow.value = null
  tick.value++
}

function stepOnce() {
  if (playEnv.episodeDone) return stopPlayback()
  const action = actFor(policy.value)(playEnv, playState, playEnv.validActions(playState))
  const result = playEnv.step(action)
  if (result.done) {
    finished.value = [...finished.value, result.info.flowResult!]
    utilSamples.value = [...utilSamples.value, result.info.avgUtilization!]
    lastFlow.value = result.info.flowResult!
    playState = playEnv.episodeDone ? result.state : playEnv.observation()
  } else {
    playState = result.state
  }
  tick.value++
}

const delay = computed(() => 1200 - speed.value * 11)
function loop() {
  stepOnce()
  if (playing.value && !playEnv.episodeDone) timer = setTimeout(loop, delay.value)
  else playing.value = false
}
function play() {
  if (playEnv.episodeDone) restartPlayback()
  playing.value = true
  loop()
}
function stopPlayback() {
  playing.value = false
  clearTimeout(timer)
}
function runToEnd() {
  stopPlayback()
  while (!playEnv.episodeDone) stepOnce()
}

watch(policy, restartPlayback)
watch([topologyName, profile], () => {
  training.value = false
  agent = new QLearningAgent(undefined, SEED)
  trainEnv = makeEnv()
  trainedEpisodes.value = 0
  progress.value = 0
  rewards = []
  curve.value = []
  comparison.value = null
  restartPlayback()
})
onBeforeUnmount(() => {
  stopPlayback()
  training.value = false
})

/* View model, recomputed after every hop. */
const view = computed(() => {
  void tick.value
  const topo = playEnv.topology
  const links: LinkView[] = spec.value.links.map(([a, b, capacity, latency]) => ({
    a, b, capacity, latency,
    utilization: Math.max(topo.edge(a, b).utilization, topo.edge(b, a).utilization),
  }))
  const done = playEnv.episodeDone
  const flow = playEnv.currentFlow
  const actions = done ? [] : playEnv.validActions(playState)
  const deterministic = policy.value !== 'random'
  const chosen = !done && deterministic && actions.length ? actFor(policy.value)(playEnv, playState, actions) : undefined
  const qValues = actions.map((a) => ({ action: a, q: agent.getQ(playState, a) }))
  return {
    links, done, flow, actions, chosen, qValues,
    state: playState,
    path: done ? [] : [...playEnv.path],
    flowNumber: playEnv.flowIndex + 1,
    unseen: policy.value === 'q_learning' && !done && !agent.hasSeen(playState, actions),
  }
})

const nodeName = (id: number) => spec.value.nodes[id]!.label
const stats = computed<Metrics>(() => summarize(finished.value, utilSamples.value))

const qRange = computed(() => {
  const qs = view.value.qValues.map((v) => v.q)
  const min = Math.min(...qs, 0)
  return { min, span: Math.max(...qs, 0) - min || 1 }
})

/* Comparison on held-out traffic */
const comparison = shallowRef<Record<PolicyName, Metrics> | null>(null)
const comparing = ref(false)
function compare() {
  comparing.value = true
  setTimeout(() => {
    const env = makeEnv()
    const out = {} as Record<PolicyName, Metrics>
    for (const name of POLICY_ORDER) {
      const act = name === 'random' ? randomPolicy(SEED) : name === 'q_learning' ? agentPolicy(agent) : actFor(name)
      out[name] = evaluate(env, act, SEED, 30)
    }
    comparison.value = out
    comparing.value = false
  }, 20)
}

const comparisonChart = computed(() => {
  const data = comparison.value
  void locale.value
  return (tk: ChartTokens): ChartConfiguration => ({
    type: 'bar',
    data: {
      labels: POLICY_ORDER.map((n) => t(`policies.${n}`)),
      datasets: [{ label: 'PDR', data: POLICY_ORDER.map((n) => data?.[n].pdr ?? 0), backgroundColor: tk.series, borderColor: tk.surface, borderWidth: 2, borderRadius: 4, maxBarThickness: 56 }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `PDR ${pct(Number(ctx.raw))}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: tk.text } },
        y: { beginAtZero: true, max: 1, grid: { color: tk.grid }, ticks: { color: tk.text, callback: (v) => pct(Number(v), 0) } },
      },
    },
  })
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ t('sim.title') }}</h1>
        <p>{{ t('sim.subtitle') }}</p>
      </div>
    </div>

    <section class="panel controls">
      <div class="field">
        <label>{{ t('sim.topology') }}</label>
        <Select v-model="topologyName" :options="topologyOptions" option-label="label" option-value="value" :disabled="training" />
      </div>
      <div class="field">
        <label>{{ t('sim.traffic') }}</label>
        <Select v-model="profile" :options="profileOptions" option-label="label" option-value="value" :disabled="training" />
      </div>
      <div class="field">
        <label>{{ t('sim.episodes') }}</label>
        <SelectButton v-model="trainTarget" :options="episodesOptions" :allow-empty="false" :disabled="training" />
      </div>
      <div class="train-action">
        <Button :label="trainedEpisodes ? t('sim.trainMore') : t('sim.train')" icon="pi pi-bolt" :loading="training" @click="train" />
        <span class="muted">{{ t('sim.trained', { count: trainedEpisodes.toLocaleString() }) }}</span>
      </div>
    </section>

    <section v-if="training || curve.length" class="panel train-panel">
      <div class="train-head">
        <h2>{{ t('sim.trainingTitle') }}</h2>
        <span class="muted num">ε = {{ fmt(agent.epsilon, 3) }} · |Q| = {{ agent.qTable.size }}</span>
      </div>
      <ProgressBar v-if="training" :value="progress" class="progress" />
      <ChartCanvas :build="rewardChart" :label="t('sim.trainingTitle')" :height="170" />
      <p class="muted note">{{ t('sim.trainingNote') }}</p>
    </section>

    <div class="sim-grid">
      <section class="panel">
        <div class="play-head">
          <SelectButton v-model="policy" :options="policyOptions" option-label="label" option-value="value" :allow-empty="false" size="small" />
          <div class="play-buttons">
            <Button v-if="!playing" icon="pi pi-play" :label="t('sim.play')" size="small" :disabled="training" @click="play" />
            <Button v-else icon="pi pi-pause" :label="t('sim.pause')" size="small" severity="secondary" @click="stopPlayback" />
            <Button icon="pi pi-step-forward" :aria-label="t('sim.step')" v-tooltip.bottom="t('sim.step')" size="small" text :disabled="training || view.done" @click="stepOnce" />
            <Button icon="pi pi-fast-forward" :aria-label="t('sim.toEnd')" v-tooltip.bottom="t('sim.toEnd')" size="small" text :disabled="training || view.done" @click="runToEnd" />
            <Button icon="pi pi-refresh" :aria-label="t('sim.restart')" v-tooltip.bottom="t('sim.restart')" size="small" text :disabled="training" @click="restartPlayback" />
          </div>
        </div>
        <div class="speed">
          <span class="muted">{{ t('sim.speed') }}</span>
          <Slider v-model="speed" :min="0" :max="100" class="slider" />
        </div>

        <Message v-if="policy === 'q_learning' && trainedEpisodes === 0" severity="warn" :closable="false" class="msg">
          {{ t('sim.untrained') }}
        </Message>

        <NetworkMap :spec="spec" :links="view.links" :path="view.path" :last-path="lastFlow?.path" :last-success="lastFlow?.success"
          :source="view.done ? undefined : view.flow.source" :destination="view.done ? undefined : view.flow.destination"
          :current="view.done ? undefined : view.state[0]" :candidates="view.actions" :chosen="view.chosen" />
      </section>

      <aside class="stack side">
        <section class="panel">
          <h2>{{ view.done ? t('sim.episodeDone') : t('sim.flowTitle', { n: view.flowNumber, total: playEnv.flows.length }) }}</h2>
          <template v-if="!view.done">
            <div class="flow-line">
              <strong>{{ nodeName(view.flow.source) }}</strong>
              <i class="pi" :class="$i18n.locale === 'he' ? 'pi-arrow-left' : 'pi-arrow-right'" />
              <strong>{{ nodeName(view.flow.destination) }}</strong>
              <Tag :value="`${fmt(view.flow.demand, 0)} Mb/s`" severity="secondary" />
            </div>
            <div class="state">
              <span class="muted">{{ t('sim.state') }}</span>
              <code>({{ nodeName(view.state[0]) }}, {{ nodeName(view.state[1]) }}, bin {{ view.state[2] }})</code>
            </div>

            <h3>{{ t('sim.decision') }}</h3>
            <p class="muted small">{{ t(`sim.policyHelp.${policy}`) }}</p>
            <ul v-if="policy === 'q_learning'" class="q-list">
              <li v-for="item in view.qValues" :key="item.action" :class="{ chosen: item.action === view.chosen }">
                <span class="q-name">{{ nodeName(item.action) }}</span>
                <span class="q-bar"><span :style="{ width: `${8 + 92 * (item.q - qRange.min) / qRange.span}%` }" /></span>
                <span class="num q-val">{{ fmt(item.q, 1) }}</span>
                <i v-if="item.action === view.chosen" class="pi pi-check" :aria-label="t('sim.chosen')" />
              </li>
            </ul>
            <ul v-else class="q-list">
              <li v-for="a in view.actions" :key="a" :class="{ chosen: a === view.chosen }">
                <span class="q-name">{{ nodeName(a) }}</span>
                <span class="num q-val">{{ fmt(playEnv.topology.edgeCost(view.state[0], a), 1) }} ms</span>
                <i v-if="a === view.chosen" class="pi pi-check" :aria-label="t('sim.chosen')" />
              </li>
            </ul>
            <p v-if="view.unseen" class="muted small"><i class="pi pi-exclamation-circle" /> {{ t('sim.unseen') }}</p>
          </template>
          <p v-else class="muted">{{ t('sim.episodeDoneText') }}</p>
        </section>

        <section class="panel">
          <h2>{{ t('sim.liveStats') }}</h2>
          <dl class="stats">
            <dt>{{ t('sim.flowsDone') }}</dt><dd class="num">{{ stats.flows }} / {{ playEnv.flows.length }}</dd>
            <dt>PDR</dt><dd class="num">{{ stats.flows ? pct(stats.pdr) : '–' }}</dd>
            <dt>{{ t('metrics.mean_latency_ms') }}</dt><dd class="num">{{ stats.flows ? `${fmt(stats.meanLatencyMs, 1)} ms` : '–' }}</dd>
            <dt>{{ t('metrics.routing_failures') }}</dt><dd class="num">{{ stats.routingFailures }}</dd>
          </dl>
          <div v-if="lastFlow" class="last">
            <i class="pi" :class="lastFlow.success ? 'pi-check-circle ok' : 'pi-times-circle bad'" />
            <span>
              {{ lastFlow.success
                ? t('sim.lastDelivered', { percent: pct(lastFlow.deliveredDemand / lastFlow.offeredDemand, 0), hops: lastFlow.hops, ms: fmt(lastFlow.latencyMs, 1) })
                : t('sim.lastFailed', { reason: t(`sim.failure.${lastFlow.failureReason}`) }) }}
            </span>
          </div>
        </section>
      </aside>
    </div>

    <section class="panel compare">
      <div class="train-head">
        <div>
          <h2>{{ t('sim.compareTitle') }}</h2>
          <p class="muted small">{{ t('sim.compareText') }}</p>
        </div>
        <Button :label="t('sim.compare')" icon="pi pi-chart-bar" severity="secondary" :loading="comparing" :disabled="training" @click="compare" />
      </div>
      <div v-if="comparison" class="grid-2">
        <ChartCanvas :build="comparisonChart" :label="t('sim.compareTitle')" :height="240" />
        <table class="data-table">
          <thead>
            <tr><th>{{ t('results.policy') }}</th><th>PDR</th><th>{{ t('metrics.mean_latency_ms') }}</th><th>{{ t('metrics.routing_failures') }}</th></tr>
          </thead>
          <tbody>
            <tr v-for="name in POLICY_ORDER" :key="name">
              <td>{{ t(`policies.${name}`) }}</td>
              <td class="num">{{ pct(comparison[name].pdr) }}</td>
              <td class="num">{{ fmt(comparison[name].meanLatencyMs, 1) }}</td>
              <td class="num">{{ comparison[name].routingFailures }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="comparison && trainedEpisodes === 0" class="muted small">{{ t('sim.untrained') }}</p>
    </section>
  </div>
</template>

<style scoped>
.controls { display: flex; flex-wrap: wrap; gap: 1rem 1.5rem; align-items: flex-end; margin-bottom: 1rem; }
.train-action { display: flex; align-items: center; gap: 0.75rem; margin-inline-start: auto; flex-wrap: wrap; }
.train-panel { margin-bottom: 1rem; }
.train-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.train-head h2 { margin: 0 0 0.25rem; }
.progress { height: 6px; margin-bottom: 0.75rem; }
.note { font-size: 0.8125rem; margin: 0.5rem 0 0; }
.sim-grid { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 1rem; margin-bottom: 1rem; }
.play-head { display: flex; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; align-items: center; }
.play-buttons { display: flex; gap: 0.25rem; align-items: center; }
.speed { display: flex; align-items: center; gap: 0.75rem; margin: 0.75rem 0; font-size: 0.8125rem; }
.slider { width: 160px; }
.msg { margin-bottom: 0.75rem; }
.side h2 { margin-bottom: 0.75rem; }
.side h3 { font-size: 0.875rem; margin: 1rem 0 0.25rem; }
.flow-line { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.state { margin-top: 0.625rem; display: grid; gap: 0.25rem; font-size: 0.8125rem; }
.state code { direction: ltr; text-align: start; }
.small { font-size: 0.8125rem; line-height: 1.5; margin: 0.25rem 0 0.5rem; }
.q-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.375rem; }
.q-list li { display: grid; grid-template-columns: 7.5rem 1fr auto 1rem; align-items: center; gap: 0.5rem; padding: 0.25rem 0.375rem; border-radius: 6px; font-size: 0.8125rem; }
.q-list li.chosen { background: color-mix(in srgb, var(--chart-series-1) 12%, transparent); font-weight: 600; }
.q-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.q-bar { height: 8px; background: var(--chart-grid); border-radius: 4px; overflow: hidden; }
.q-bar span { display: block; height: 100%; background: var(--chart-series-1); border-radius: 4px; }
.q-val { text-align: end; }
.q-list .pi-check { color: var(--chart-series-1); }
.stats { display: grid; grid-template-columns: 1fr auto; gap: 0.375rem 1rem; margin: 0; }
.stats dt { color: var(--app-text-muted); }
.stats dd { margin: 0; font-weight: 600; }
.last { display: flex; gap: 0.5rem; align-items: flex-start; margin-top: 0.875rem; font-size: 0.8125rem; line-height: 1.5; }
.last .ok { color: var(--chart-series-3); }
.last .bad { color: var(--load-3); }
.compare .grid-2 { align-items: center; }
@media (max-width: 1100px) {
  .sim-grid { grid-template-columns: 1fr; }
}
</style>
