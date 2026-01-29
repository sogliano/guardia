import api from './api'

export async function exportReport(format: string, filters: Record<string, unknown> = {}): Promise<Blob> {
  const { data } = await api.post('/reports/export', { format, filters }, { responseType: 'blob' })
  return data
}
