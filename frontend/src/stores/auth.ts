import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/auth'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  async function fetchProfile() {
    loading.value = true
    try {
      const { data } = await api.get<User>('/auth/me')
      user.value = data
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  function clearProfile() {
    user.value = null
  }

  return { user, loading, isAuthenticated, fetchProfile, clearProfile }
})
