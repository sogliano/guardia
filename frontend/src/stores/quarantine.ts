import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Case } from '@/types/case'
import {
  fetchQuarantine as fetchQuarantineApi,
  fetchQuarantineEmailDetail,
  releaseQuarantine,
  keepQuarantine,
  deleteQuarantine,
} from '@/services/quarantineService'
import type { QuarantineEmailDetail } from '@/services/quarantineService'
import { useGlobalFiltersStore } from '@/stores/globalFilters'

export const useQuarantineStore = defineStore('quarantine', () => {
  const items = ref<Case[]>([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const globalFilters = useGlobalFiltersStore()

  const selectedId = ref<string | null>(null)
  const emailDetail = ref<QuarantineEmailDetail | null>(null)
  const detailLoading = ref(false)
  const actionLoading = ref(false)

  async function fetchQuarantined() {
    loading.value = true
    error.value = null
    try {
      const gf = globalFilters.filterParams
      const result = await fetchQuarantineApi({ page: page.value, size: size.value, ...gf })
      items.value = result.items
      total.value = result.total
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load quarantine'
    } finally {
      loading.value = false
    }
  }

  async function selectItem(caseId: string) {
    selectedId.value = caseId
    detailLoading.value = true
    try {
      emailDetail.value = await fetchQuarantineEmailDetail(caseId)
    } catch {
      emailDetail.value = null
    } finally {
      detailLoading.value = false
    }
  }

  async function release(caseId: string, reason?: string) {
    actionLoading.value = true
    try {
      await releaseQuarantine(caseId, reason)
      selectedId.value = null
      emailDetail.value = null
      await fetchQuarantined()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Release failed'
    } finally {
      actionLoading.value = false
    }
  }

  async function keep(caseId: string, reason?: string) {
    actionLoading.value = true
    try {
      await keepQuarantine(caseId, reason)
      selectedId.value = null
      emailDetail.value = null
      await fetchQuarantined()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Keep failed'
    } finally {
      actionLoading.value = false
    }
  }

  async function remove(caseId: string, reason?: string) {
    actionLoading.value = true
    try {
      await deleteQuarantine(caseId, reason)
      selectedId.value = null
      emailDetail.value = null
      await fetchQuarantined()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Delete failed'
    } finally {
      actionLoading.value = false
    }
  }

  function setPage(p: number) {
    page.value = p
    fetchQuarantined()
  }

  watch(() => globalFilters.filterParams, () => {
    page.value = 1
    fetchQuarantined()
  }, { deep: true })

  return {
    items, total, page, size, loading, error,
    selectedId, emailDetail, detailLoading, actionLoading,
    fetchQuarantined, selectItem, setPage, release, keep, remove,
  }
})
