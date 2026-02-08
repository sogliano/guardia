import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { useGlobalFiltersStore } from './globalFilters'
import { fetchMonitoringStats } from '@/services/monitoringService'
import type {
  HeuristicsMonitoringData,
  MLMonitoringData,
  MonitoringData,
} from '@/types/monitoring'

export const useMonitoringStore = defineStore('monitoring', () => {
  const data = ref<MonitoringData | MLMonitoringData | HeuristicsMonitoringData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeTab = ref<'llm' | 'ml' | 'heuristics' | 'score-analysis'>('heuristics')
  const globalFilters = useGlobalFiltersStore()

  let initialized = false

  async function fetchMonitoring() {
    initialized = true
    if (activeTab.value === 'score-analysis') return
    loading.value = true
    error.value = null
    try {
      data.value = await fetchMonitoringStats(activeTab.value, globalFilters.filterParams)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load monitoring data'
    } finally {
      loading.value = false
    }
  }

  watch(
    () => globalFilters.filterParams,
    () => {
      if (initialized) {
        fetchMonitoring()
      }
    },
    { deep: true },
  )

  watch(
    () => activeTab.value,
    () => {
      if (initialized) {
        fetchMonitoring()
      }
    },
  )

  const kpi = computed(() => data.value?.kpi ?? null)
  const tokenTrend = computed(() => {
    if ('token_trend' in (data.value ?? {})) {
      return (data.value as MonitoringData).token_trend
    }
    return []
  })
  const latencyDistribution = computed(() => {
    if ('latency_distribution' in (data.value ?? {})) {
      return (data.value as MonitoringData).latency_distribution
    }
    return []
  })
  const scoreAgreement = computed(() => {
    if ('score_agreement' in (data.value ?? {})) {
      return (data.value as MonitoringData | MLMonitoringData).score_agreement
    }
    return null
  })
  const costBreakdown = computed(() => {
    if ('cost_breakdown' in (data.value ?? {})) {
      return (data.value as MonitoringData).cost_breakdown
    }
    return []
  })
  const recentAnalyses = computed(() => data.value?.recent_analyses ?? [])

  return {
    data,
    loading,
    error,
    activeTab,
    kpi,
    tokenTrend,
    latencyDistribution,
    scoreAgreement,
    costBreakdown,
    recentAnalyses,
    fetchMonitoring,
  }
})
