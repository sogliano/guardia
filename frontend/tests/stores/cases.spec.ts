import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCasesStore } from '@/stores/cases'
import * as caseService from '@/services/caseService'

vi.mock('@/services/caseService')
vi.mock('@/stores/globalFilters', () => ({
  useGlobalFiltersStore: () => ({
    filterParams: {},
  }),
}))

describe('Cases Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetchCases', () => {
    it('should fetch cases successfully', async () => {
      const mockCases = [
        {
          id: '123',
          case_number: 'CASE-001',
          final_score: 0.85,
          risk_level: 'high',
          verdict: 'quarantined',
          status: 'open',
        },
      ]

      vi.mocked(caseService.fetchCases).mockResolvedValue({
        items: mockCases,
        total: 1,
        page: 1,
        size: 20,
      })

      const store = useCasesStore()
      await store.fetchCases()

      expect(store.cases).toEqual(mockCases)
      expect(store.total).toBe(1)
      expect(store.loading).toBe(false)
      expect(store.error).toBe(null)
    })

    it('should handle fetch error', async () => {
      vi.mocked(caseService.fetchCases).mockRejectedValue(new Error('API error'))

      const store = useCasesStore()
      await store.fetchCases()

      expect(store.cases).toEqual([])
      expect(store.error).toBe('API error')
      expect(store.loading).toBe(false)
    })

    it('should set loading state correctly', async () => {
      vi.mocked(caseService.fetchCases).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  items: [],
                  total: 0,
                  page: 1,
                  size: 20,
                }),
              100,
            ),
          ),
      )

      const store = useCasesStore()
      const promise = store.fetchCases()

      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('computed properties', () => {
    it('should filter quarantined cases', async () => {
      vi.mocked(caseService.fetchCases).mockResolvedValue({
        items: [
          { id: '1', status: 'quarantined', verdict: 'quarantined' } as any,
          { id: '2', status: 'open', verdict: 'warn' } as any,
          { id: '3', status: 'quarantined', verdict: 'quarantined' } as any,
        ],
        total: 3,
        page: 1,
        size: 20,
      })

      const store = useCasesStore()
      await store.fetchCases()

      expect(store.quarantinedCases).toHaveLength(2)
      expect(store.quarantinedCases[0].status).toBe('quarantined')
    })

    it('should filter blocked cases', async () => {
      vi.mocked(caseService.fetchCases).mockResolvedValue({
        items: [
          { id: '1', status: 'open', verdict: 'blocked' } as any,
          { id: '2', status: 'resolved', verdict: 'blocked' } as any,
          { id: '3', status: 'open', verdict: 'warn' } as any,
        ],
        total: 3,
        page: 1,
        size: 20,
      })

      const store = useCasesStore()
      await store.fetchCases()

      expect(store.blockedCases).toHaveLength(1)
      expect(store.blockedCases[0].id).toBe('1')
    })
  })

  describe('pagination', () => {
    it('should change page and refetch', async () => {
      vi.mocked(caseService.fetchCases).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        size: 20,
      })

      const store = useCasesStore()
      store.setPage(2)

      expect(store.page).toBe(2)
      expect(caseService.fetchCases).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
      )
    })

    it('should change size and reset page', async () => {
      vi.mocked(caseService.fetchCases).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        size: 50,
      })

      const store = useCasesStore()
      store.page = 3
      store.setSize(50)

      expect(store.size).toBe(50)
      expect(store.page).toBe(1)
    })
  })

  describe('filters', () => {
    it('should apply filters and reset page', async () => {
      vi.mocked(caseService.fetchCases).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        size: 20,
      })

      const store = useCasesStore()
      store.page = 3
      store.setFilters({ risk_level: 'high', status: 'open' })

      expect(store.page).toBe(1)
      expect(store.filters).toEqual({ risk_level: 'high', status: 'open' })
      expect(caseService.fetchCases).toHaveBeenCalledWith(
        expect.objectContaining({
          risk_level: 'high',
          status: 'open',
        }),
      )
    })
  })
})
