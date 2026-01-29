import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGlobalFiltersStore = defineStore('globalFilters', () => {
  const dateRange = ref<Date[] | null>(null)
  const sender = ref('')

  const filterParams = computed(() => {
    const params: Record<string, string> = {}
    if (dateRange.value && dateRange.value.length >= 1 && dateRange.value[0]) {
      params.date_from = dateRange.value[0].toISOString()
    }
    if (dateRange.value && dateRange.value.length >= 2 && dateRange.value[1]) {
      const end = new Date(dateRange.value[1])
      end.setHours(23, 59, 59, 999)
      params.date_to = end.toISOString()
    }
    if (sender.value.trim()) params.sender = sender.value.trim()
    return params
  })

  const hasActiveFilters = computed(() => {
    return (dateRange.value && dateRange.value.length > 0) || sender.value.trim() !== ''
  })

  function setDateRange(range: Date[] | null) {
    dateRange.value = range
  }

  function setDatePreset(preset: string) {
    const now = new Date()
    let from: Date
    switch (preset) {
      case '24h':
        from = new Date(now.getTime() - 24 * 60 * 60 * 1000)
        break
      case '7d':
        from = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case '30d':
        from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        break
      default:
        dateRange.value = null
        return
    }
    dateRange.value = [from, now]
  }

  function setSender(value: string) {
    sender.value = value
  }

  function clearFilters() {
    dateRange.value = null
    sender.value = ''
  }

  return {
    dateRange, sender, filterParams, hasActiveFilters,
    setDateRange, setDatePreset, setSender, clearFilters,
  }
})
