import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

export function requireRole(...roles: UserRole[]) {
  return (to: RouteLocationNormalized) => {
    const authStore = useAuthStore()
    if (!authStore.user || !roles.includes(authStore.user.role)) {
      return { name: 'dashboard' }
    }
  }
}
