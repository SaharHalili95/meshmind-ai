import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig(({ mode }) => ({
  // GitHub Pages serves the site from /<repo>/; local dev is served from the root.
  base: mode === 'pages' ? (process.env.VITE_BASE ?? '/meshmind-ai/') : '/',
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: { port: 5174 },
  test: { environment: 'jsdom' },
}))
