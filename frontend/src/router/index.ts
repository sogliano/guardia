import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'cases',
          name: 'cases',
          component: () => import('@/views/CasesView.vue'),
        },
        {
          path: 'cases/:id',
          name: 'case-detail',
          component: () => import('@/views/CaseDetailView.vue'),
          props: true,
        },
        {
          path: 'quarantine',
          name: 'quarantine',
          component: () => import('@/views/QuarantineView.vue'),
        },
        {
          path: 'emails',
          name: 'emails',
          component: () => import('@/views/EmailExplorerView.vue'),
        },
        {
          path: 'policies',
          name: 'policies',
          component: () => import('@/views/PoliciesView.vue'),
        },
        {
          path: 'alerts',
          name: 'alerts',
          component: () => import('@/views/AlertsView.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/ReportsView.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
        },
        {
          path: 'fp-review',
          name: 'fp-review',
          component: () => import('@/views/FPReviewView.vue'),
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/NotificationsView.vue'),
        },
      ],
    },
  ],
})

export default router
