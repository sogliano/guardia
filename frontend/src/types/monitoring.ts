export interface MonitoringKPI {
  total_calls: number
  avg_latency_ms: number
  p95_latency_ms: number
  total_tokens: number
  estimated_cost: number
  error_count: number
  error_rate: number
  prev_total_calls: number
}

export interface TokenTrendPoint {
  date: string
  prompt_tokens: number
  completion_tokens: number
}

export interface LatencyBucket {
  range: string
  count: number
}

export interface ScoreAgreement {
  agree_pct: number
  minor_diff_pct: number
  major_divergence_pct: number
  total: number
}

export interface CostBreakdownPoint {
  date: string
  model: string
  cost: number
}

export interface RecentLLMAnalysis {
  time: string
  case_number: number | null
  sender: string | null
  llm_score: number | null
  final_score: number | null
  tokens: number | null
  latency_ms: number | null
  status: string
  model?: string | null
  threat_category?: string | null
  explanation_summary?: string | null
}

export interface MonitoringData {
  kpi: MonitoringKPI
  token_trend: TokenTrendPoint[]
  latency_distribution: LatencyBucket[]
  score_agreement: ScoreAgreement
  cost_breakdown: CostBreakdownPoint[]
  recent_analyses: RecentLLMAnalysis[]
}

// ML Monitoring Types
export interface MLMonitoringKPI {
  total_calls: number
  avg_latency_ms: number
  p95_latency_ms: number
  avg_confidence: number
  error_count: number
  error_rate: number
  prev_total_calls: number
}

export interface ScoreDistributionBucket {
  range: string
  count: number
}

export interface ConfidenceAccuracyPoint {
  confidence: number
  accuracy: number
}

export interface LatencyTrendPoint {
  date: string
  avg_latency_ms: number
}

export interface RecentMLAnalysis {
  time: string
  case_number: number | null
  sender: string | null
  ml_score: number | null
  final_score: number | null
  confidence: number | null
  latency_ms: number | null
  status: string
}

export interface MLMonitoringData {
  kpi: MLMonitoringKPI
  score_distribution: ScoreDistributionBucket[]
  confidence_accuracy: ConfidenceAccuracyPoint[]
  latency_trend: LatencyTrendPoint[]
  score_agreement: ScoreAgreement
  recent_analyses: RecentMLAnalysis[]
}

// Heuristics Monitoring Types
export interface HeuristicsMonitoringKPI {
  total_runs: number
  avg_latency_ms: number
  p95_latency_ms: number
  high_score_rate: number
  zero_score_rate: number
  prev_total_runs: number
}

export interface TopRulePoint {
  rule_name: string
  count: number
}

export interface RecentHeuristicsAnalysis {
  time: string
  case_number: number | null
  sender: string | null
  heuristic_score: number | null
  final_score: number | null
  triggered_rules: string[]
  latency_ms: number | null
}

export interface HeuristicsMonitoringData {
  kpi: HeuristicsMonitoringKPI
  top_triggered_rules: TopRulePoint[]
  score_distribution: ScoreDistributionBucket[]
  score_agreement: ScoreAgreement
  recent_analyses: RecentHeuristicsAnalysis[]
}
