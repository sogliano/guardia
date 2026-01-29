export const RISK_OPTIONS = ['Low', 'Medium', 'High', 'Critical']
export const ACTION_OPTIONS = ['Allowed', 'Warned', 'Quarantined', 'Blocked']
export const STATUS_OPTIONS = ['Pending', 'Analyzing', 'Analyzed', 'Quarantined', 'Resolved']
export const DATE_OPTIONS = ['Last 24h', 'Last 7 days', 'Last 30 days', 'All time']

export const DATE_RANGE_OPTIONS = [
  { label: 'All time', value: 'all' as const },
  { label: 'Last 24h', value: '24h' as const },
  { label: 'Last 7 days', value: '7d' as const },
  { label: 'Last 30 days', value: '30d' as const },
]

export function dateRangeToParams(range: string): { date_from?: string; date_to?: string } {
  if (range === 'all') return {}
  const now = new Date()
  const to = now.toISOString()
  let from: Date
  switch (range) {
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
      return {}
  }
  return { date_from: from.toISOString(), date_to: to }
}
