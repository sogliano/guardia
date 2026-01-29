export interface DashboardStats {
  total_emails_analyzed: number
  emails_today: number
  blocked_count: number
  quarantined_count: number
  warned_count: number
  allowed_count: number
  avg_score: number
  pending_cases: number
}

export interface ChartDataPoint {
  label: string
  value: number
}

export interface ThreatCategoryCount {
  category: string
  count: number
}

export interface PipelineHealthStats {
  avg_duration_ms: number
  p95_duration_ms: number
  success_rate: number
  stage_avg_ms: Record<string, number>
}

export interface RecentCaseItem {
  id: string
  subject: string | null
  sender: string
  score: number | null
  verdict: string | null
  created_at: string
}

export interface ActiveAlertItem {
  id: string
  rule_name: string
  severity: string
  message: string
  created_at: string
}

export interface VerdictTrendPoint {
  date: string
  allow: number
  warn: number
  quarantine: number
  block: number
}

export interface ScoreBucket {
  range: string
  count: number
}

export interface DashboardData {
  stats: DashboardStats
  risk_distribution: ChartDataPoint[]
  daily_trend: ChartDataPoint[]
  threat_categories: ThreatCategoryCount[]
  pipeline_health: PipelineHealthStats | null
  recent_cases: RecentCaseItem[]
  active_alerts: ActiveAlertItem[]
  verdict_trend: VerdictTrendPoint[]
  score_distribution: ScoreBucket[]
}
