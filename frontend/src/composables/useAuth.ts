import { useClerk } from '@clerk/vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const clerk = useClerk()
  const router = useRouter()
  const authStore = useAuthStore()

  async function logout() {
    await clerk.signOut()
    authStore.clearProfile()
    router.push({ name: 'login' })
  }

  return { logout }
}
