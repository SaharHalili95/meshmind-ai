<script setup lang="ts">
import Button from 'primevue/button'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { toggleLocale } from '@/i18n'

const { t } = useI18n()
const route = useRoute()
const mobileOpen = ref(false)

const nav = [
  { to: '/', label: 'nav.results', icon: 'pi pi-chart-bar' },
  { to: '/simulator', label: 'nav.simulator', icon: 'pi pi-play-circle' },
]
const guideNav = [
  { to: '/architecture', label: 'nav.architecture', icon: 'pi pi-share-alt' },
  { to: '/learning', label: 'nav.learning', icon: 'pi pi-graduation-cap' },
  { to: '/troubleshooting', label: 'nav.troubleshooting', icon: 'pi pi-wrench' },
  { to: '/about', label: 'nav.about', icon: 'pi pi-book' },
]

watch(() => route.fullPath, () => (mobileOpen.value = false))
</script>

<template>
  <div class="shell">
    <aside class="sidebar" :class="{ open: mobileOpen }">
      <div class="brand">
        <span class="logo"><i class="pi pi-sitemap" /></span>
        <span>MeshMind AI</span>
      </div>
      <nav>
        <RouterLink v-for="item in nav" :key="item.to" :to="item.to" class="nav-link" exact-active-class="active">
          <i :class="item.icon" />
          <span>{{ t(item.label) }}</span>
        </RouterLink>
        <div class="nav-divider" />
        <RouterLink v-for="item in guideNav" :key="item.to" :to="item.to" class="nav-link" exact-active-class="active">
          <i :class="item.icon" />
          <span>{{ t(item.label) }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-footer">
        <a href="https://github.com/SaharHalili95/meshmind-ai" target="_blank" rel="noopener" class="gh">
          <i class="pi pi-github" /> GitHub
        </a>
        <span dir="ltr">{{ t('layout.footer') }}</span>
      </div>
    </aside>
    <div v-if="mobileOpen" class="backdrop" @click="mobileOpen = false" />

    <div class="main">
      <div class="demo-banner">
        <i class="pi pi-info-circle" />
        {{ t('layout.banner') }}
      </div>
      <header class="topbar">
        <Button class="menu-toggle" icon="pi pi-bars" text rounded :aria-label="t('nav.openMenu')" @click="mobileOpen = true" />
        <div class="spacer" />
        <Button :label="t('nav.switchLanguage')" icon="pi pi-globe" text size="small" :aria-label="t('nav.switchLanguageLabel')" @click="toggleLocale" />
      </header>
      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell { display: flex; min-height: 100vh; }
.sidebar {
  width: 240px; flex-shrink: 0; background: var(--app-sidebar); color: var(--app-sidebar-text);
  display: flex; flex-direction: column; padding: 1.25rem 0.75rem; position: sticky; top: 0; height: 100vh;
}
.brand { display: flex; align-items: center; gap: 0.625rem; color: #fff; font-weight: 700; font-size: 1.125rem; padding: 0 0.5rem 1.5rem; }
.logo { width: 32px; height: 32px; border-radius: 8px; background: var(--app-accent); display: grid; place-items: center; font-size: 0.9rem; }
nav { display: flex; flex-direction: column; gap: 0.25rem; }
.nav-link {
  display: flex; align-items: center; gap: 0.75rem; padding: 0.625rem 0.75rem; border-radius: 8px;
  color: inherit; text-decoration: none; font-weight: 500;
}
.nav-link:hover { background: var(--app-sidebar-active); color: #fff; }
.nav-link.active { background: var(--app-sidebar-active); color: #fff; box-shadow: inset 3px 0 0 var(--app-accent); }
:global([dir='rtl']) .nav-link.active { box-shadow: inset -3px 0 0 var(--app-accent); }
.nav-divider { height: 1px; background: rgb(255 255 255 / 0.08); margin: 0.5rem 0.75rem; }
.sidebar-footer { margin-top: auto; padding: 0 0.5rem; font-size: 0.75rem; display: grid; gap: 0.5rem; }
.sidebar-footer span { opacity: 0.6; }
.gh { color: inherit; text-decoration: none; display: inline-flex; gap: 0.5rem; align-items: center; font-size: 0.8125rem; }
.gh:hover { color: #fff; }
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.demo-banner { background: #e8f1fc; color: #1a4f8f; padding: 0.5rem 1.5rem; font-size: 0.8125rem; display: flex; gap: 0.5rem; align-items: center; }
@media (prefers-color-scheme: dark) {
  .demo-banner { background: #10223a; color: #a9c8f0; }
}
.topbar { display: flex; align-items: center; padding: 0.75rem 1.5rem; background: var(--app-surface); border-bottom: 1px solid var(--app-border); }
.spacer { flex: 1; }
.content { padding: 1.75rem 1.5rem 3rem; max-width: 1280px; width: 100%; margin: 0 auto; }
.menu-toggle, .backdrop { display: none; }

@media (max-width: 900px) {
  .sidebar { position: fixed; z-index: 30; inset-inline-start: 0; transform: translateX(-100%); transition: transform 0.2s; }
  :global([dir='rtl']) .sidebar { transform: translateX(100%); }
  .sidebar.open { transform: none; }
  .backdrop { display: block; position: fixed; inset: 0; background: rgb(0 0 0 / 0.4); z-index: 20; }
  .menu-toggle { display: inline-flex; }
  .content { padding: 1.25rem 1rem 2rem; }
  .topbar { padding: 0.5rem 1rem; }
}
</style>
