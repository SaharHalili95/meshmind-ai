<script setup lang="ts">
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import Tag from 'primevue/tag'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { flows, lanes, nodes, type DiagramNode, type NodeId } from '@/content/architecture'
import { pick } from '@/content/localized'
import type { Locale } from '@/i18n'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as Locale)
const rtl = computed(() => lang.value === 'he')

/* Diagram geometry (SVG user units). */
const LANE_WIDTH = 200
const NODE_WIDTH = 172
const NODE_HEIGHT = 46
const ROW_HEIGHT = 66
const TOP = 60
const WIDTH = LANE_WIDTH * lanes.length
const HEIGHT = TOP + ROW_HEIGHT * 4 + 8

const laneX = (lane: number) => (rtl.value ? lanes.length - 1 - lane : lane) * LANE_WIDTH
const nodeBox = (node: DiagramNode) => ({ x: laneX(node.lane) + (LANE_WIDTH - NODE_WIDTH) / 2, y: TOP + node.row * ROW_HEIGHT })
const byId = new Map(nodes.map((n) => [n.id, n]))

const flowOptions = computed(() => flows.map((f) => ({ value: f.id, label: pick(f.title, lang.value) })))
const flowId = ref(flows[0]!.id)
const flow = computed(() => flows.find((f) => f.id === flowId.value)!)
const stepIndex = ref(0)
const step = computed(() => flow.value.steps[stepIndex.value]!)
const activeNode = computed(() => byId.get(step.value.node)!)
const visited = computed(() => new Set<NodeId>(flow.value.steps.slice(0, stepIndex.value + 1).map((s) => s.node)))
const involved = computed(() => new Set<NodeId>(flow.value.steps.map((s) => s.node)))

const pinned = ref<NodeId | null>(null)
const detailNode = computed(() => byId.get(pinned.value ?? activeNode.value.id)!)
function pin(id: NodeId) {
  stop()
  pinned.value = pinned.value === id ? null : id
}

const arrow = computed(() => {
  if (stepIndex.value === 0) return null
  const from = byId.get(flow.value.steps[stepIndex.value - 1]!.node)!
  const to = activeNode.value
  if (from.id === to.id) return null
  const a = nodeBox(from)
  const b = nodeBox(to)
  const ax = a.x + NODE_WIDTH / 2
  const ay = a.y + NODE_HEIGHT / 2
  const bx = b.x + NODE_WIDTH / 2
  const by = b.y + NODE_HEIGHT / 2
  const dx = bx - ax
  const dy = by - ay
  const edge = (cx: number, cy: number, sx: number, sy: number) => {
    const scale = Math.min(Math.abs(NODE_WIDTH / 2 / (sx || 1e-9)), Math.abs(NODE_HEIGHT / 2 / (sy || 1e-9)))
    return { x: cx + sx * scale, y: cy + sy * scale }
  }
  const start = edge(ax, ay, dx, dy)
  const end = edge(bx, by, -dx, -dy)
  return { x1: start.x, y1: start.y, x2: end.x, y2: end.y }
})

const playing = ref(false)
let timer: ReturnType<typeof setInterval> | undefined
function stop() {
  playing.value = false
  clearInterval(timer)
}
function play() {
  if (stepIndex.value === flow.value.steps.length - 1) stepIndex.value = 0
  pinned.value = null
  playing.value = true
  timer = setInterval(() => {
    if (stepIndex.value < flow.value.steps.length - 1) stepIndex.value++
    else stop()
  }, 2400)
}
function go(delta: number) {
  stop()
  pinned.value = null
  stepIndex.value = Math.min(Math.max(stepIndex.value + delta, 0), flow.value.steps.length - 1)
}
function select(index: number) {
  stop()
  pinned.value = null
  stepIndex.value = index
}
watch(flowId, () => {
  stop()
  pinned.value = null
  stepIndex.value = 0
})
onBeforeUnmount(stop)

const lifecycle = ['start', 'hop', 'delivered', 'failed', 'next'] as const
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ t('architecture.title') }}</h1>
        <p>{{ t('architecture.subtitle') }}</p>
      </div>
    </div>

    <section class="panel">
      <div class="flow-head">
        <SelectButton v-model="flowId" :options="flowOptions" option-label="label" option-value="value" :allow-empty="false" />
        <div class="flow-buttons">
          <Button icon="pi pi-angle-double-left" text rounded :aria-label="t('architecture.prev')" :disabled="stepIndex === 0" @click="go(-1)" />
          <Button v-if="!playing" icon="pi pi-play" :label="t('architecture.play')" size="small" @click="play" />
          <Button v-else icon="pi pi-pause" :label="t('architecture.pause')" size="small" severity="secondary" @click="stop" />
          <Button icon="pi pi-angle-double-right" text rounded :aria-label="t('architecture.next')" :disabled="stepIndex === flow.steps.length - 1" @click="go(1)" />
        </div>
      </div>
      <p class="muted">{{ pick(flow.summary, lang) }}</p>

      <div class="diagram-wrap">
        <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="diagram" role="img" :aria-label="t('architecture.diagramLabel')">
          <defs>
            <marker id="arch-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" class="arrow-head" />
            </marker>
          </defs>
          <g v-for="(lane, i) in lanes" :key="lane.id">
            <rect :x="laneX(i) + 4" y="4" :width="LANE_WIDTH - 8" :height="HEIGHT - 8" rx="12" class="lane" />
            <text :x="laneX(i) + LANE_WIDTH / 2" y="34" class="lane-title">{{ pick(lane.title, lang) }}</text>
          </g>
          <line v-if="arrow" :x1="arrow.x1" :y1="arrow.y1" :x2="arrow.x2" :y2="arrow.y2" class="flow-arrow" marker-end="url(#arch-arrow)" />
          <g v-for="node in nodes" :key="node.id" class="node" tabindex="0" role="button"
            :class="{ active: node.id === activeNode.id && !pinned, pinned: node.id === pinned, visited: visited.has(node.id), dim: !involved.has(node.id) }"
            @click="pin(node.id)" @keydown.enter="pin(node.id)">
            <rect :x="nodeBox(node).x" :y="nodeBox(node).y" :width="NODE_WIDTH" :height="NODE_HEIGHT" rx="8" />
            <text :x="nodeBox(node).x + NODE_WIDTH / 2" :y="nodeBox(node).y + NODE_HEIGHT / 2 + 5">{{ node.label }}</text>
          </g>
        </svg>
      </div>

      <div class="below">
        <ol class="steps">
          <li v-for="(s, i) in flow.steps" :key="i" :class="{ current: i === stepIndex, done: i < stepIndex }" @click="select(i)">
            <span class="num-badge">{{ i + 1 }}</span>
            <span>{{ pick(s.text, lang) }}</span>
          </li>
        </ol>
        <aside class="detail">
          <div class="detail-head">
            <code>{{ detailNode.label }}</code>
            <Tag :value="pick(lanes[detailNode.lane]!.title, lang)" severity="secondary" />
          </div>
          <p>{{ pick(detailNode.plain, lang) }}</p>
          <dl>
            <dt>{{ t('architecture.api') }}</dt><dd><code>{{ detailNode.api }}</code></dd>
            <dt>{{ t('architecture.file') }}</dt>
            <dd><a :href="`https://github.com/SaharHalili95/meshmind-ai/blob/main/${detailNode.code}`" target="_blank" rel="noopener"><code>{{ detailNode.code }}</code></a></dd>
            <template v-if="detailNode.test">
              <dt>{{ t('architecture.tests') }}</dt><dd><code>{{ detailNode.test }}</code></dd>
            </template>
          </dl>
          <p class="muted hint">{{ pinned ? t('architecture.unpinHint') : t('architecture.pinHint') }}</p>
        </aside>
      </div>
    </section>

    <section class="panel layers">
      <h2>{{ t('architecture.layersTitle') }}</h2>
      <p class="muted">{{ t('architecture.layersIntro') }}</p>
      <ol class="layer-list">
        <li v-for="(lane, i) in lanes" :key="lane.id">
          <span class="badge">{{ i + 1 }}</span>
          <div>
            <strong>{{ pick(lane.title, lang) }}</strong>
            <span class="muted"> · {{ pick(lane.role, lang) }}</span>
          </div>
        </li>
      </ol>
    </section>

    <div class="grid-2">
      <section class="panel">
        <h2>{{ t('architecture.mdpTitle') }}</h2>
        <dl class="mdp">
          <dt>{{ t('architecture.mdp.state') }}</dt><dd>{{ t('architecture.mdp.stateText') }}</dd>
          <dt>{{ t('architecture.mdp.action') }}</dt><dd>{{ t('architecture.mdp.actionText') }}</dd>
          <dt>{{ t('architecture.mdp.reward') }}</dt><dd>{{ t('architecture.mdp.rewardText') }}</dd>
          <dt>{{ t('architecture.mdp.end') }}</dt><dd>{{ t('architecture.mdp.endText') }}</dd>
        </dl>
        <div class="formula">Q(s,a) ← Q(s,a) + α · [ r + γ · max Q(s′,a′) − Q(s,a) ]
α = 0.1   γ = 0.95   max Q(s′,·) = 0 when the flow ended</div>
      </section>
      <section class="panel">
        <h2>{{ t('architecture.lifecycleTitle') }}</h2>
        <ol class="lifecycle">
          <li v-for="stage in lifecycle" :key="stage" :class="stage">
            <strong>{{ t(`architecture.lifecycle.${stage}`) }}</strong>
            <span class="muted">{{ t(`architecture.lifecycle.${stage}Text`) }}</span>
          </li>
        </ol>
        <div class="formula">cost(e) = latency(e) + penalty(e)
penalty(e) = latency(e) · ((ρ − 0.8) / 0.2)²   if ρ &gt; 0.8, else 0</div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.flow-head { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.flow-buttons { display: flex; align-items: center; gap: 0.25rem; }
.diagram-wrap { overflow-x: auto; margin: 0.5rem 0 1rem; }
.diagram { width: 100%; min-width: 760px; height: auto; display: block; }
.lane { fill: color-mix(in srgb, var(--app-accent) 4%, transparent); stroke: var(--app-border); }
.lane-title { font-size: 13px; font-weight: 650; text-anchor: middle; fill: var(--app-text-muted); }
.node { cursor: pointer; }
.node rect { fill: var(--app-surface); stroke: var(--app-border); stroke-width: 1.5; transition: all 0.2s; }
.node text { direction: ltr; unicode-bidi: isolate; font-size: 13px; text-anchor: middle; fill: var(--app-text); font-family: ui-monospace, 'SF Mono', Menlo, monospace; pointer-events: none; }
.node.dim { opacity: 0.45; }
.node.visited rect { stroke: color-mix(in srgb, var(--app-accent) 55%, transparent); }
.node.active rect, .node.pinned rect { fill: var(--app-accent); stroke: var(--app-accent); }
.node.active text, .node.pinned text { fill: #fff; font-weight: 700; }
.node:focus-visible rect { stroke: var(--app-text); stroke-width: 2.5; }
.flow-arrow { stroke: var(--app-accent); stroke-width: 2.5; }
.arrow-head { fill: var(--app-accent); }
.below { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 1rem; }
.steps { margin: 0; padding: 0; list-style: none; display: grid; gap: 0.375rem; }
.steps li { display: flex; gap: 0.75rem; align-items: flex-start; padding: 0.5rem 0.625rem; border-radius: 8px; cursor: pointer; line-height: 1.5; opacity: 0.6; }
.steps li.done { opacity: 0.85; }
.steps li.current { opacity: 1; background: color-mix(in srgb, var(--app-accent) 10%, transparent); }
.num-badge { flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; font-size: 0.75rem; font-weight: 700; background: var(--app-border); }
.steps li.current .num-badge { background: var(--app-accent); color: #fff; }
.detail { border: 1px solid var(--app-border); border-radius: 10px; padding: 1rem; align-self: start; }
.detail-head { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
.detail-head code { font-weight: 700; font-size: 0.9375rem; }
.detail p { line-height: 1.55; }
.detail dl { display: grid; gap: 0.25rem; margin: 0; }
.detail dt { color: var(--app-text-muted); font-size: 0.75rem; font-weight: 600; margin-top: 0.375rem; }
.detail dd { margin: 0; font-size: 0.8125rem; }
.detail a { color: var(--app-accent); }
.hint { font-size: 0.75rem; margin-bottom: 0; }
.layers { margin: 1rem 0; }
.layer-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.625rem; }
.layer-list li { display: flex; gap: 0.75rem; align-items: baseline; line-height: 1.5; }
.badge { flex-shrink: 0; width: 26px; height: 26px; border-radius: 8px; display: grid; place-items: center; background: color-mix(in srgb, var(--app-accent) 12%, transparent); color: var(--app-accent); font-weight: 700; }
.mdp { display: grid; grid-template-columns: max-content 1fr; gap: 0.5rem 1rem; margin: 0 0 1rem; line-height: 1.55; }
.mdp dt { font-weight: 600; color: var(--app-text-muted); }
.mdp dd { margin: 0; }
.lifecycle { list-style: none; margin: 0 0 1rem; padding: 0; display: grid; gap: 0.5rem; }
.lifecycle li { display: grid; gap: 0.125rem; padding-inline-start: 0.75rem; border-inline-start: 3px solid var(--app-border); line-height: 1.5; }
.lifecycle li.delivered { border-color: var(--chart-series-3); }
.lifecycle li.failed { border-color: var(--load-3); }
.lifecycle li.hop, .lifecycle li.start { border-color: var(--chart-series-1); }
@media (max-width: 1000px) {
  .below { grid-template-columns: 1fr; }
}
</style>
