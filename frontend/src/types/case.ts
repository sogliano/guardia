export type CaseStatus = 'pending' | 'analyzing' | 'analyzed' | 'quarantined' | 'resolved'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type Verdict = 'allowed' | 'warned' | 'quarantined' | 'blocked'
export type PipelineStage = 'heuristic' | 'ml' | 'llm'
export type ThreatCategory =
  | 'bec_impersonation'
  | 'credential_phishing'
  | 'malware_payload'
  | 'generic_phishing'
  | 'clean'

export interface Case {
  id: string
  case_number: number
  email_id: string
  status: CaseStatus
  final_score: number | null
  risk_level: RiskLevel | null
  verdict: Verdict | null
  threat_category: ThreatCategory | null
  pipeline_duration_ms: number | null
  resolved_by: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
  email_subject: string | null
  email_sender: string | null
  email_received_at: string | null
}

export interface CaseList {
  items: Case[]
  total: number
  page: number
  size: number
}

export interface CaseResolve {
  verdict: string
}

export interface Analysis {
  id: string
  case_id: string
  stage: PipelineStage
  score: number | null
  confidence: number | null
  explanation: string | null
  metadata: Record<string, unknown>
  execution_time_ms: number | null
  created_at: string
  evidences?: Evidence[]
}

export interface Evidence {
  id: string
  analysis_id: string
  type: string
  severity: string
  description: string
  raw_data: Record<string, unknown>
  created_at: string
}

export interface CaseNote {
  id: string
  case_id: string
  author_id: string
  author_name: string | null
  content: string
  created_at: string
}

export interface CaseNoteCreate {
  content: string
}

export interface QuarantineAction {
  id: string
  case_id: string
  action: string
  reason: string | null
  performed_by: string
  created_at: string
}

export interface QuarantineActionCreate {
  action: string
  reason?: string
}

export interface FPReview {
  id: string
  case_id: string
  decision: string
  reviewer_id: string
  notes: string | null
  created_at: string
}

export interface FPReviewCreate {
  decision: string
  notes?: string
}

export interface CaseEmail {
  sender_email: string
  sender_name: string | null
  recipient_email: string
  recipients_cc: string[]
  subject: string | null
  body_text: string | null
  body_html: string | null
  headers: Record<string, unknown>
  urls: string[]
  attachments: Array<Record<string, unknown>>
  auth_results: Record<string, unknown>
  received_at: string | null
}

export interface CaseDetail extends Case {
  email: CaseEmail | null
  analyses: Analysis[]
  notes: CaseNote[]
}
