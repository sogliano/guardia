export function scoreColor(score: number | null): string {
  if (score === null) return '#6B7280'
  if (score >= 0.8) return '#EF4444'
  if (score >= 0.6) return '#F97316'
  if (score >= 0.3) return '#F59E0B'
  return '#22C55E'
}

export function riskColor(level: string | null): string {
  if (!level) return '#6B7280'
  const colors: Record<string, string> = {
    critical: '#EF4444',
    high: '#F97316',
    medium: '#F59E0B',
    low: '#22C55E',
  }
  return colors[level] ?? '#6B7280'
}

export function riskBg(level: string | null): string {
  if (!level) return 'rgba(107,114,128,0.15)'
  const colors: Record<string, string> = {
    critical: 'rgba(239,68,68,0.15)',
    high: 'rgba(249,115,22,0.15)',
    medium: 'rgba(245,158,11,0.15)',
    low: 'rgba(34,197,94,0.15)',
  }
  return colors[level] ?? 'rgba(107,114,128,0.15)'
}

export function actionColor(verdict: string | null): string {
  if (!verdict) return '#6B7280'
  const colors: Record<string, string> = {
    blocked: '#EF4444',
    quarantined: '#F97316',
    warned: '#F59E0B',
    allowed: '#22C55E',
  }
  return colors[verdict] ?? '#6B7280'
}

export function actionBg(verdict: string | null): string {
  if (!verdict) return 'rgba(107,114,128,0.15)'
  const colors: Record<string, string> = {
    blocked: 'rgba(239,68,68,0.15)',
    quarantined: 'rgba(249,115,22,0.15)',
    warned: 'rgba(245,158,11,0.15)',
    allowed: 'rgba(34,197,94,0.15)',
  }
  return colors[verdict] ?? 'rgba(107,114,128,0.15)'
}

export function statusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: '#F59E0B',
    analyzing: '#3B82F6',
    analyzed: '#00D4FF',
    quarantined: '#F97316',
    resolved: '#6B7280',
  }
  return colors[status] ?? '#6B7280'
}

export function statusBg(status: string): string {
  const colors: Record<string, string> = {
    pending: 'rgba(245,158,11,0.15)',
    analyzing: 'rgba(59,130,246,0.15)',
    analyzed: 'rgba(0,212,255,0.15)',
    quarantined: 'rgba(249,115,22,0.15)',
    resolved: 'rgba(107,114,128,0.15)',
  }
  return colors[status] ?? 'rgba(107,114,128,0.15)'
}
