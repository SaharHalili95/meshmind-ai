<script setup lang="ts">
defineProps<{ label: string; value: string; caption?: string; icon: string }>()
</script>

<template>
  <div class="tile">
    <div class="icon"><i :class="icon" /></div>
    <div>
      <div class="label">{{ label }}</div>
      <div class="value">{{ value }}</div>
      <div v-if="caption" class="caption">{{ caption }}</div>
    </div>
  </div>
</template>

<style scoped>
.tile {
  display: flex; gap: 0.875rem; align-items: flex-start; background: var(--app-surface);
  border: 1px solid var(--app-border); border-radius: 12px; padding: 1.125rem 1.25rem;
}
.icon {
  width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center; flex-shrink: 0;
  background: color-mix(in srgb, var(--app-accent) 12%, transparent); color: var(--app-accent);
}
.label { color: var(--app-text-muted); font-size: 0.8125rem; font-weight: 500; }
.value { font-size: 1.5rem; font-weight: 650; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; margin-top: 0.125rem; }
.caption { color: var(--app-text-muted); font-size: 0.75rem; margin-top: 0.125rem; }
</style>
