import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Case } from '@/types/case'
import { fetchCases as fetchCasesApi } from '@/services/caseService'
import { useGlobalFiltersStore } from '@/stores/globalFilters'

export const useCasesStore = defineStore('cases', () => {
  const cases = ref<Case[]>([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const globalFilters = useGlobalFiltersStore()
  const filters = ref<{
    status?: string
    risk_level?: string
    verdict?: string
    date_from?: string
    date_to?: string
    search?: string
  }>({})

  async function fetchCases() {
    loading.value = true
    error.value = null
    try {
      const gf = globalFilters.filterParams
      const result = await fetchCasesApi({
        page: page.value,
        size: size.value,
        ...filters.value,
        ...gf,
      })
      cases.value = result.items
      total.value = result.total
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load cases'
    } finally {
      loading.value = false
    }
  }

  function setPage(p: number) {
    page.value = p
    fetchCases()
  }

  function setFilters(f: typeof filters.value) {
    filters.value = f
    page.value = 1
    fetchCases()
  }

  watch(() => globalFilters.filterParams, () => {
    page.value = 1
    fetchCases()
  }, { deep: true })

  return { cases, total, page, size, loading, error, filters, fetchCases, setPage, setFilters }
})
