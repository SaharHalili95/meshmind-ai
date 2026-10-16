<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TopologySpec } from '@/sim/topology'

export interface LinkView {
  a: number
  b: number
  /** Highest utilization of the two directions. */
  utilization: number
  latency: number
  capacity: number
}

const props = defineProps<{
  spec: TopologySpec
  links: LinkView[]
  path: number[]
  lastPath?: number[]
  lastSuccess?: boolean
  source?: number
  destination?: number
  current?: number
  candidates?: number[]
  chosen?: number
}>()

const { t } = useI18n()
const pos = computed(() => new Map(props.spec.nodes.map((n) => [n.id, n])))
const [width, height] = props.spec.viewBox

const loadClass = (u: number) => (u >= 1 ? 'l3' : u >= 0.8 ? 'l2' : u >= 0.5 ? 'l1' : 'l0')
const strokeWidth = (u: number) => 3 + 6 * Math.min(u, 1.5) / 1.5

const points = (nodes: number[]) => nodes.map((id) => `${pos.value.get(id)!.x},${pos.value.get(id)!.y}`).join(' ')

function midpoint(a: number, b: number) {
  const p = pos.value.get(a)!
  const q = pos.value.get(b)!
  return { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 }
}
</script>

<template>
  <div class="map-wrap">
    <svg :viewBox="`0 0 ${width} ${height}`" class="map" role="img" :aria-label="t('sim.mapLabel')">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" class="arrow-head" />
        </marker>
      </defs>

      <g class="links">
        <g v-for="link in links" :key="`${link.a}-${link.b}`">
          <line :x1="pos.get(link.a)!.x" :y1="pos.get(link.a)!.y" :x2="pos.get(link.b)!.x" :y2="pos.get(link.b)!.y"
            class="link" :class="loadClass(link.utilization)" :stroke-width="strokeWidth(link.utilization)">
            <title>{{ spec.nodes[link.a]!.label }} ↔ {{ spec.nodes[link.b]!.label }} · {{ t('sim.utilization') }} {{ Math.round(link.utilization * 100) }}% · {{ link.latency }} ms · cap {{ link.capacity }}</title>
          </line>
          <text :x="midpoint(link.a, link.b).x" :y="midpoint(link.a, link.b).y - 7" class="link-label">{{ link.latency }}</text>
        </g>
      </g>

      <polyline v-if="lastPath && lastPath.length > 1" :points="points(lastPath)" class="last-path" :class="{ failed: !lastSuccess }" />
      <polyline v-if="path.length > 1" :points="points(path)" class="path" marker-end="url(#arrow)" />

      <g v-if="current !== undefined && candidates">
        <line v-for="c in candidates" :key="c" :x1="pos.get(current)!.x" :y1="pos.get(current)!.y" :x2="pos.get(c)!.x" :y2="pos.get(c)!.y"
          class="candidate" :class="{ chosen: c === chosen }" />
      </g>

      <g v-for="node in spec.nodes" :key="node.id" class="node"
        :class="{ source: node.id === source, destination: node.id === destination, current: node.id === current }">
        <circle v-if="node.id === current" :cx="node.x" :cy="node.y" r="26" class="pulse" />
        <circle :cx="node.x" :cy="node.y" r="17" class="dot" />
        <text :x="node.x" :y="node.y + 4" class="short">{{ node.short }}</text>
        <text v-if="spec.name === 'abilene'" :x="node.x" :y="node.y + 34" class="label">{{ node.label }}</text>
      </g>
    </svg>

    <div class="legend">
      <span><i class="sw l0" /> &lt; 50%</span>
      <span><i class="sw l1" /> 50–80%</span>
      <span><i class="sw l2" /> 80–100%</span>
      <span><i class="sw l3" /> ≥ 100% · {{ t('sim.legendLoss') }}</span>
      <span><i class="ring src" /> {{ t('sim.legendSource') }}</span>
      <span><i class="ring dst" /> {{ t('sim.legendDestination') }}</span>
      <span><i class="line path-sw" /> {{ t('sim.legendPath') }}</span>
    </div>
  </div>
</template>

<style scoped>
.map-wrap { width: 100%; }
.map { width: 100%; height: auto; display: block; direction: ltr; }
.link { stroke-linecap: round; transition: stroke 0.25s, stroke-width 0.25s; }
.l0 { stroke: var(--load-0); }
.l1 { stroke: var(--load-1); }
.l2 { stroke: var(--load-2); }
.l3 { stroke: var(--load-3); }
.link-label { font-size: 11px; fill: var(--app-text-muted); text-anchor: middle; paint-order: stroke; stroke: var(--app-surface); stroke-width: 3px; }
.path { fill: none; stroke: var(--chart-series-1); stroke-width: 4; stroke-linejoin: round; stroke-linecap: round; }
.arrow-head { fill: var(--chart-series-1); }
.last-path { fill: none; stroke: var(--chart-series-1); stroke-width: 3; stroke-dasharray: 6 6; opacity: 0.45; }
.last-path.failed { stroke: var(--load-3); }
.candidate { stroke: var(--chart-series-1); stroke-width: 2; stroke-dasharray: 3 5; opacity: 0.6; }
.candidate.chosen { stroke-width: 3; stroke-dasharray: none; opacity: 0.9; }
.dot { fill: var(--map-node); stroke: var(--map-node-stroke); stroke-width: 2; }
.short { font-size: 11px; font-weight: 700; text-anchor: middle; fill: var(--app-text); pointer-events: none; }
.label { font-size: 12px; text-anchor: middle; fill: var(--app-text-muted); paint-order: stroke; stroke: var(--app-surface); stroke-width: 4px; }
.node.source .dot { stroke: var(--chart-series-1); stroke-width: 4; }
.node.destination .dot { stroke: var(--app-text); stroke-width: 3; stroke-dasharray: 4 3; }
.node.current .dot { fill: var(--chart-series-1); }
.node.current .short { fill: #fff; }
.pulse { fill: none; stroke: var(--chart-series-1); stroke-width: 2; opacity: 0.5; animation: pulse 1.2s ease-out infinite; transform-box: fill-box; transform-origin: center; }
@keyframes pulse { from { transform: scale(0.7); opacity: 0.7; } to { transform: scale(1.25); opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .pulse { animation: none; } }
.legend { display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; font-size: 0.75rem; color: var(--app-text-muted); margin-top: 0.5rem; }
.legend span { display: inline-flex; align-items: center; gap: 0.375rem; }
.sw { width: 18px; height: 6px; border-radius: 3px; display: inline-block; }
.sw.l0 { background: var(--load-0); }
.sw.l1 { background: var(--load-1); }
.sw.l2 { background: var(--load-2); }
.sw.l3 { background: var(--load-3); }
.ring { width: 12px; height: 12px; border-radius: 50%; display: inline-block; background: var(--map-node); }
.ring.src { border: 3px solid var(--chart-series-1); }
.ring.dst { border: 2px dashed var(--app-text); }
.line { width: 18px; height: 4px; border-radius: 2px; display: inline-block; }
.path-sw { background: var(--chart-series-1); }
</style>
