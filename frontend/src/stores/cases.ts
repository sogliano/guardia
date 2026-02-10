import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Case } from '@/types/case'
import { fetchCases as fetchCasesApi } from '@/services/caseService'
import { useGlobalFiltersStore } from '@/stores/globalFilters'

export const useCasesStore = defineStore('cases', () => {
  const globalFilters = useGlobalFiltersStore()

  // ── All Cases tab state ──
  const cases = ref<Case[]>([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const filters = ref<{
    status?: string | string[]
    risk_level?: string
    verdict?: string | string[]
    date_from?: string
    date_to?: string
    search?: string
  }>({})

  // ── Needs Action tab state ──
  const needsActionCases = ref<Case[]>([])
  const needsActionTotal = ref(0)
  const needsActionPage = ref(1)
  const needsActionSize = ref(20)
  const needsActionLoading = ref(false)

  // ── Quarantine & Blocked tab state ──
  const qbCases = ref<Case[]>([])
  const qbTotal = ref(0)
  const qbLoading = ref(false)

  // ── Legacy computeds (kept for backward compat) ──
  const quarantinedCases = computed(() =>
    cases.value.filter(c => c.status === 'quarantined')
  )

  const blockedCases = computed(() =>
    cases.value.filter(c => c.verdict === 'blocked' && c.status !== 'resolved')
  )

  const quarantineAndBlockedCases = computed(() =>
    qbCases.value
  )

  // ── All Cases fetch ──
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

  // ── Needs Action fetch (server-side: status=analyzed + quarantined) ──
  async function fetchNeedsAction(extraFilters?: Record<string, unknown>) {
    needsActionLoading.value = true
    try {
      const gf = globalFilters.filterParams
      const result = await fetchCasesApi({
        page: needsActionPage.value,
        size: needsActionSize.value,
        status: ['analyzed', 'quarantined'],
        ...gf,
        ...extraFilters,
      })
      needsActionCases.value = result.items
      needsActionTotal.value = result.total
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load needs-action cases'
    } finally {
      needsActionLoading.value = false
    }
  }

  // ── Quarantine & Blocked fetch ──
  // Two fetches: status=quarantined + verdict=blocked (excluding resolved), deduplicated
  async function fetchQuarantineBlocked() {
    qbLoading.value = true
    try {
      const gf = globalFilters.filterParams
      const [quarantined, blocked] = await Promise.all([
        fetchCasesApi({ status: ['quarantined'], size: 100, ...gf }),
        fetchCasesApi({ verdict: ['blocked'], size: 100, ...gf }),
      ])

      // Merge and deduplicate, exclude resolved from blocked results
      const map = new Map<string, Case>()
      for (const c of quarantined.items) {
        map.set(c.id, c)
      }
      for (const c of blocked.items) {
        if (c.status !== 'resolved' && !map.has(c.id)) {
          map.set(c.id, c)
        }
      }
      qbCases.value = Array.from(map.values())
      qbTotal.value = qbCases.value.length
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load quarantine cases'
    } finally {
      qbLoading.value = false
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

  function setNeedsActionPage(p: number) {
    needsActionPage.value = p
    fetchNeedsAction()
  }

  function setNeedsActionSize(s: number) {
    needsActionSize.value = s
    needsActionPage.value = 1
    fetchNeedsAction()
  }

  watch(() => globalFilters.filterParams, () => {
    page.value = 1
    fetchCases()
  }, { deep: true })

  return {
    // All Cases
    cases, total, page, size, loading, error, filters,
    fetchCases, setPage, setSize, setFilters,
    quarantinedCases, blockedCases, quarantineAndBlockedCases,
    // Needs Action
    needsActionCases, needsActionTotal, needsActionPage, needsActionSize, needsActionLoading,
    fetchNeedsAction, setNeedsActionPage, setNeedsActionSize,
    // Quarantine & Blocked
    qbCases, qbTotal, qbLoading,
    fetchQuarantineBlocked,
  }
})
