import api from './api'
import type { HeuristicsMonitoringData, MLMonitoringData, MonitoringData } from '@/types/monitoring'

export async function fetchMonitoringStats(
  tab: 'llm' | 'ml' | 'heuristics',
  params?: Record<string, string>,
): Promise<MonitoringData | MLMonitoringData | HeuristicsMonitoringData> {
  const allParams = { ...params, tab }
  const { data } = await api.get('/monitoring', { params: allParams })
  return data
}
