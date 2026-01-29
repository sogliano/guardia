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
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/NotificationsView.vue'),
        },
      ],
    },
  ],
})

export default router
