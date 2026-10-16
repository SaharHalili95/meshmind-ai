import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'
import PrimeVue from 'primevue/config'
import Tooltip from 'primevue/tooltip'
import { createApp } from 'vue'
import 'primeicons/primeicons.css'
import App from './App.vue'
import { i18n } from './i18n'
import router from './router'
import './styles/main.css'

// Aura's default primary is emerald; use blue so components match the brand and chart series 1.
const MeshMindPreset = definePreset(Aura, {
  semantic: {
    primary: Object.fromEntries(
      [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map((step) => [step, `{blue.${step}}`]),
    ),
  },
})

createApp(App)
  .use(i18n)
  .use(router)
  .use(PrimeVue, { theme: { preset: MeshMindPreset, options: { darkModeSelector: 'system' } } })
  .directive('tooltip', Tooltip)
  .mount('#app')
