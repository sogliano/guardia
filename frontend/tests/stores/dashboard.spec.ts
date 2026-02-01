import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore } from '@/stores/dashboard'
import * as dashboardService from '@/services/dashboardService'

vi.mock('@/services/dashboardService')
vi.mock('@/stores/globalFilters', () => ({
  useGlobalFiltersStore: () => ({
    filterParams: {},
  }),
}))

describe('Dashboard Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetchDashboard', () => {
    it('should fetch dashboard stats successfully', async () => {
      const mockStats = {
        total_cases: 150,
        high_risk_cases: 45,
        quarantined_cases: 12,
        avg_score: 0.42,
        verdict_breakdown: {
          allowed: 100,
          warn: 35,
          quarantined: 12,
          blocked: 3,
        },
      }

      vi.mocked(dashboardService.fetchDashboardStats).mockResolvedValue(mockStats)

      const store = useDashboardStore()
      await store.fetchDashboard()

      expect(store.data).toEqual(mockStats)
      expect(store.loading).toBe(false)
      expect(store.error).toBe(null)
    })

    it('should handle fetch error', async () => {
      vi.mocked(dashboardService.fetchDashboardStats).mockRejectedValue(
        new Error('API error'),
      )

      const store = useDashboardStore()
      await store.fetchDashboard()

      expect(store.data).toBe(null)
      expect(store.error).toBe('API error')
      expect(store.loading).toBe(false)
    })

    it('should set loading state correctly', async () => {
      vi.mocked(dashboardService.fetchDashboardStats).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  total_cases: 0,
                  high_risk_cases: 0,
                  quarantined_cases: 0,
                  avg_score: 0,
                }),
              100,
            ),
          ),
      )

      const store = useDashboardStore()
      const promise = store.fetchDashboard()

      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
    })
  })
})
