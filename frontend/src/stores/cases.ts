import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Case } from '@/types/case'
import {
  fetchCases as fetchCasesApi,
  fetchQuarantineEmailDetail,
  releaseQuarantine,
  keepQuarantine,
  deleteQuarantine,
} from '@/services/caseService'
import type { QuarantineEmailDetail } from '@/services/caseService'
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

  // Quarantine state
  const quarantineSelectedId = ref<string | null>(null)
  const quarantineEmailDetail = ref<QuarantineEmailDetail | null>(null)
  const quarantineDetailLoading = ref(false)
  const quarantineActionLoading = ref(false)

  const quarantinedCases = computed(() =>
    cases.value.filter(c => c.status === 'quarantined')
  )

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

  function setSize(s: number) {
    size.value = s
    page.value = 1
    fetchCases()
  }

  function setFilters(f: typeof filters.value) {
    filters.value = f
    page.value = 1
    fetchCases()
  }

  // Quarantine actions
  async function selectQuarantineItem(caseId: string) {
    quarantineSelectedId.value = caseId
    quarantineDetailLoading.value = true
    try {
      quarantineEmailDetail.value = await fetchQuarantineEmailDetail(caseId)
    } catch {
      quarantineEmailDetail.value = null
    } finally {
      quarantineDetailLoading.value = false
    }
  }

  function clearQuarantineSelection() {
    quarantineSelectedId.value = null
    quarantineEmailDetail.value = null
  }

  async function releaseCase(caseId: string, reason?: string) {
    quarantineActionLoading.value = true
    try {
      await releaseQuarantine(caseId, reason)
      clearQuarantineSelection()
      await fetchCases()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Release failed'
    } finally {
      quarantineActionLoading.value = false
    }
  }

  async function keepQuarantinedCase(caseId: string, reason?: string) {
    quarantineActionLoading.value = true
    try {
      await keepQuarantine(caseId, reason)
      clearQuarantineSelection()
      await fetchCases()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Keep failed'
    } finally {
      quarantineActionLoading.value = false
    }
  }

  async function deleteQuarantinedCase(caseId: string, reason?: string) {
    quarantineActionLoading.value = true
    try {
      await deleteQuarantine(caseId, reason)
      clearQuarantineSelection()
      await fetchCases()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Delete failed'
    } finally {
      quarantineActionLoading.value = false
    }
  }

  watch(() => globalFilters.filterParams, () => {
    page.value = 1
    fetchCases()
  }, { deep: true })

  return {
    cases, total, page, size, loading, error, filters,
    fetchCases, setPage, setSize, setFilters,
    // Quarantine
    quarantinedCases,
    quarantineSelectedId, quarantineEmailDetail,
    quarantineDetailLoading, quarantineActionLoading,
    selectQuarantineItem, clearQuarantineSelection,
    releaseCase, keepQuarantinedCase, deleteQuarantinedCase,
  }
})
