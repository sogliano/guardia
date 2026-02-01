import { ref } from 'vue'

export interface FilterConfig {
  riskOptions: string[]
  actionOptions: string[]
  statusOptions: string[]
}

/**
 * Composable for managing multi-select filters on case/email lists.
 * Provides reusable filter state and logic for search, risk, action, and status.
 */
export function useFilters(config: FilterConfig) {
  // Multi-select filters
  const filterRisk = ref<string[]>(config.riskOptions.slice())
  const filterAction = ref<string[]>(config.actionOptions.slice())
  const filterStatus = ref<string[]>(config.statusOptions.slice())
  const searchQuery = ref<string>('')
  const dateRange = ref<string | undefined>()

  // Helper: check if filter is active (not all selected)
  const isFilterActive = (selected: string[], all: string[]) => {
    return selected.length > 0 && selected.length < all.length
  }

  // Apply filters to case array
  const applyFilters = <T extends {
    risk_level?: string
    verdict?: string
    status?: string
    email_subject?: string
    email_sender?: string
  }>(items: T[]): T[] => {
    let result = items

    // Search query
    const q = searchQuery.value.trim().toLowerCase()
    if (q) {
      result = result.filter(item =>
        (item.email_subject?.toLowerCase().includes(q)) ||
        (item.email_sender?.toLowerCase().includes(q))
      )
    }

    // Risk filter
    if (isFilterActive(filterRisk.value, config.riskOptions)) {
      const selected = filterRisk.value.map(r => r.toLowerCase())
      result = result.filter(item =>
        item.risk_level && selected.includes(item.risk_level.toLowerCase())
      )
    }

    // Action/Verdict filter
    if (isFilterActive(filterAction.value, config.actionOptions)) {
      const selected = filterAction.value.map(a => a.toLowerCase())
      result = result.filter(item =>
        item.verdict && selected.includes(item.verdict.toLowerCase())
      )
    }

    // Status filter
    if (isFilterActive(filterStatus.value, config.statusOptions)) {
      const selected = filterStatus.value.map(s => s.toLowerCase())
      result = result.filter(item =>
        item.status && selected.includes(item.status.toLowerCase())
      )
    }

    return result
  }

  // Reset all filters
  const resetFilters = () => {
    filterRisk.value = config.riskOptions.slice()
    filterAction.value = config.actionOptions.slice()
    filterStatus.value = config.statusOptions.slice()
    searchQuery.value = ''
    dateRange.value = undefined
  }

  return {
    filterRisk,
    filterAction,
    filterStatus,
    searchQuery,
    dateRange,
    applyFilters,
    resetFilters,
    isFilterActive,
  }
}
