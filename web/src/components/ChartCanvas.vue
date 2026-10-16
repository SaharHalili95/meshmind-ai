<script setup lang="ts">
import {
  BarController, BarElement, CategoryScale, Chart, type ChartConfiguration, Filler, Legend, LinearScale,
  LineController, LineElement, PointElement, Tooltip,
} from 'chart.js'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

Chart.register(BarController, BarElement, CategoryScale, Filler, Legend, LinearScale, LineController, LineElement, PointElement, Tooltip)

export interface ChartTokens {
  series: [string, string, string, string]
  grid: string
  text: string
  surface: string
}

const props = defineProps<{
  /** Builds the config from resolved theme tokens, so light and dark each get their own validated colors. */
  build: (tokens: ChartTokens) => ChartConfiguration
  label: string
  height?: number
}>()

const canvas = ref<HTMLCanvasElement>()
let chart: Chart | undefined
const media = window.matchMedia('(prefers-color-scheme: dark)')

function tokens(): ChartTokens {
  const css = getComputedStyle(document.documentElement)
  const v = (name: string) => css.getPropertyValue(name).trim()
  return {
    series: [v('--chart-series-1'), v('--chart-series-2'), v('--chart-series-3'), v('--chart-series-4')],
    grid: v('--chart-grid'),
    text: v('--chart-text'),
    surface: v('--chart-surface'),
  }
}

function render() {
  chart?.destroy()
  if (canvas.value) chart = new Chart(canvas.value, props.build(tokens()))
}

onMounted(() => {
  render()
  media.addEventListener('change', render)
})
onBeforeUnmount(() => {
  media.removeEventListener('change', render)
  chart?.destroy()
})
watch(() => props.build, render)
</script>

<template>
  <div class="chart" :style="{ height: `${height ?? 280}px` }">
    <canvas ref="canvas" role="img" :aria-label="label" />
  </div>
</template>

<style scoped>
.chart { position: relative; width: 100%; }
</style>
