import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { i18n } from '@/i18n'

declare module 'vue-router' {
  interface RouteMeta {
    /** i18n key of the page title. */
    title?: string
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      { path: '', name: 'results', component: () => import('@/views/ResultsView.vue'), meta: { title: 'nav.results' } },
      { path: 'simulator', name: 'simulator', component: () => import('@/views/SimulatorView.vue'), meta: { title: 'nav.simulator' } },
      { path: 'architecture', name: 'architecture', component: () => import('@/views/ArchitectureView.vue'), meta: { title: 'nav.architecture' } },
      { path: 'learning', name: 'learning', component: () => import('@/views/LearningView.vue'), meta: { title: 'nav.learning' } },
      { path: 'troubleshooting', name: 'troubleshooting', component: () => import('@/views/TroubleshootingView.vue'), meta: { title: 'nav.troubleshooting' } },
      { path: 'about', name: 'about', component: () => import('@/views/AboutView.vue'), meta: { title: 'nav.about' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  // Static hosting (GitHub Pages) cannot rewrite deep links, so the site uses hash URLs.
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${i18n.global.t(to.meta.title)} · MeshMind AI` : 'MeshMind AI'
})

export default router
