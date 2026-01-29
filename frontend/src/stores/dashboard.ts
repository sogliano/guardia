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

  watch(() => globalFilters.filterParams, () => {
    fetchDashboard()
  }, { deep: true })

  return { data, loading, error, fetchDashboard }
})
