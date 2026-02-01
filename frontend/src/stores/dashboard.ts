import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { DashboardData } from '@/types/dashboard'
import { fetchDashboardStats } from '@/services/dashboardService'
import { useGlobalFiltersStore } from '@/stores/globalFilters'

export const useDashboardStore = defineStore('dashboard', () => {
  const data = ref<DashboardData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const globalFilters = useGlobalFiltersStore()

  async function fetchDashboard() {
    loading.value = true
    error.value = null
    try {
      data.value = await fetchDashboardStats(globalFilters.filterParams)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load dashboard'
    } finally {
      loading.value = false
    }
  }

  let initialized = false

  watch(() => globalFilters.filterParams, () => {
    if (initialized) {
      fetchDashboard()
    }
  }, { deep: true })

  const originalFetch = fetchDashboard
  fetchDashboard = async function() {
    initialized = true
    return originalFetch()
  }

  return { data, loading, error, fetchDashboard }
})
