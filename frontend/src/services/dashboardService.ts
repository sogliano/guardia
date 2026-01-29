import api from './api'
import type { DashboardData } from '@/types/dashboard'

export async function fetchDashboardStats(
  params?: Record<string, string>
): Promise<DashboardData> {
  const { data } = await api.get<DashboardData>('/dashboard', { params })
  return data
}
