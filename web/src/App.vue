<script setup lang="ts">
import { usePrimeVue } from 'primevue/config'
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const primevue = usePrimeVue()

// PrimeVue's own built-in texts (empty dropdowns, filters) follow the app language.
watch(locale, (value) => {
  const hebrew = value === 'he'
  Object.assign(primevue.config.locale ?? {}, {
    emptyMessage: hebrew ? 'אין אפשרויות' : 'No available options',
    emptyFilterMessage: hebrew ? 'לא נמצאו תוצאות' : 'No results found',
  })
}, { immediate: true })
</script>

<template>
  <RouterView />
</template>
