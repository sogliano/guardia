import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  fetchCases,
  fetchCase,
  fetchCaseDetail,
  resolveCase,
  releaseQuarantine,
  keepQuarantine,
  deleteQuarantine,
} from '@/services/caseService'
import api from '@/services/api'

vi.mock('@/services/api')

describe('Case Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchCases', () => {
    it('should fetch cases with filters', async () => {
      const mockResponse = {
        data: {
          items: [{ id: '123', case_number: 'CASE-001' }],
          total: 1,
          page: 1,
          size: 20,
        },
      }

      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await fetchCases({
        page: 1,
        size: 20,
        risk_level: 'high',
      })

      expect(api.get).toHaveBeenCalledWith('/cases', {
        params: {
          page: 1,
          size: 20,
          risk_level: 'high',
        },
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('fetchCase', () => {
    it('should fetch case by ID', async () => {
      const mockCase = { id: '123', case_number: 'CASE-001' }
      vi.mocked(api.get).mockResolvedValue({ data: mockCase })

      const result = await fetchCase('123')

      expect(api.get).toHaveBeenCalledWith('/cases/123')
      expect(result).toEqual(mockCase)
    })
  })

  describe('fetchCaseDetail', () => {
    it('should fetch case detail by ID', async () => {
      const mockDetail = {
        id: '123',
        case_number: 'CASE-001',
        analyses: [],
        email: {},
      }
      vi.mocked(api.get).mockResolvedValue({ data: mockDetail })

      const result = await fetchCaseDetail('123')

      expect(api.get).toHaveBeenCalledWith('/cases/123/detail')
      expect(result).toEqual(mockDetail)
    })
  })

  describe('resolveCase', () => {
    it('should resolve case with verdict', async () => {
      const mockCase = { id: '123', status: 'resolved' }
      vi.mocked(api.post).mockResolvedValue({ data: mockCase })

      const result = await resolveCase('123', 'confirmed_fp')

      expect(api.post).toHaveBeenCalledWith('/cases/123/resolve', {
        verdict: 'confirmed_fp',
      })
      expect(result).toEqual(mockCase)
    })
  })

  describe('quarantine actions', () => {
    it('should release quarantined email', async () => {
      const mockCase = { id: '123', status: 'released' }
      vi.mocked(api.post).mockResolvedValue({ data: mockCase })

      const result = await releaseQuarantine('123', 'false positive')

      expect(api.post).toHaveBeenCalledWith(
        '/quarantine/123/release',
        null,
        {
          params: { reason: 'false positive' },
        },
      )
      expect(result).toEqual(mockCase)
    })

    it('should keep quarantined email', async () => {
      const mockCase = { id: '123', status: 'quarantined' }
      vi.mocked(api.post).mockResolvedValue({ data: mockCase })

      const result = await keepQuarantine('123', 'confirmed threat')

      expect(api.post).toHaveBeenCalledWith('/quarantine/123/keep', null, {
        params: { reason: 'confirmed threat' },
      })
      expect(result).toEqual(mockCase)
    })

    it('should delete quarantined email', async () => {
      const mockCase = { id: '123', status: 'deleted' }
      vi.mocked(api.post).mockResolvedValue({ data: mockCase })

      const result = await deleteQuarantine('123', 'spam')

      expect(api.post).toHaveBeenCalledWith('/quarantine/123/delete', null, {
        params: { reason: 'spam' },
      })
      expect(result).toEqual(mockCase)
    })
  })
})
