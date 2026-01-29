import api from './api'
import type {
  Case,
  CaseDetail,
  CaseList,
  CaseNote,
  CaseNoteCreate,
  Analysis,
  FPReview,
  FPReviewCreate,
} from '@/types/case'

export async function fetchCases(params: {
  page?: number
  size?: number
  status?: string
  risk_level?: string
  verdict?: string
  date_from?: string
  date_to?: string
  search?: string
  sender?: string
}): Promise<CaseList> {
  const { data } = await api.get<CaseList>('/cases', { params })
  return data
}

export async function fetchCase(id: string): Promise<Case> {
  const { data } = await api.get<Case>(`/cases/${id}`)
  return data
}

export async function fetchCaseDetail(id: string): Promise<CaseDetail> {
  const { data } = await api.get<CaseDetail>(`/cases/${id}/detail`)
  return data
}

export async function resolveCase(id: string, verdict: string): Promise<Case> {
  const { data } = await api.post<Case>(`/cases/${id}/resolve`, { verdict })
  return data
}

export async function addCaseNote(caseId: string, body: CaseNoteCreate): Promise<CaseNote> {
  const { data } = await api.post<CaseNote>(`/cases/${caseId}/notes`, body)
  return data
}

export async function updateCaseNote(
  caseId: string,
  noteId: string,
  content: string,
): Promise<CaseNote> {
  const { data } = await api.patch<CaseNote>(`/cases/${caseId}/notes/${noteId}`, { content })
  return data
}

export async function fetchAnalyses(caseId: string): Promise<Analysis[]> {
  const { data } = await api.get<Analysis[]>(`/cases/${caseId}/analyses`)
  return data
}

export async function createFPReview(caseId: string, body: FPReviewCreate): Promise<FPReview> {
  const { data } = await api.post<FPReview>(`/cases/${caseId}/fp-review`, body)
  return data
}

// Quarantine actions
export interface QuarantineEmailDetail {
  case_id: string
  subject: string | null
  sender_email: string
  sender_name: string | null
  recipient_email: string
  reply_to: string | null
  received_at: string | null
  message_id: string
  auth_results: Record<string, unknown>
  body_preview: string | null
  urls: unknown[]
  attachments: unknown[]
  risk_level: string | null
  final_score: number | null
  threat_category: string | null
  ai_explanation: string | null
}

export async function fetchQuarantineEmailDetail(caseId: string): Promise<QuarantineEmailDetail> {
  const { data } = await api.get<QuarantineEmailDetail>(`/quarantine/${caseId}/email`)
  return data
}

export async function releaseQuarantine(caseId: string, reason?: string): Promise<Case> {
  const { data } = await api.post<Case>(`/quarantine/${caseId}/release`, null, {
    params: { reason },
  })
  return data
}

export async function keepQuarantine(caseId: string, reason?: string): Promise<Case> {
  const { data } = await api.post<Case>(`/quarantine/${caseId}/keep`, null, {
    params: { reason },
  })
  return data
}

export async function deleteQuarantine(caseId: string, reason?: string): Promise<Case> {
  const { data } = await api.post<Case>(`/quarantine/${caseId}/delete`, null, {
    params: { reason },
  })
  return data
}
