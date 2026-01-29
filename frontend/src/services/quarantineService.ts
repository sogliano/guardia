import api from './api'
import type { Case, CaseList } from '@/types/case'

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

export async function fetchQuarantine(params: {
  page?: number
  size?: number
  date_from?: string
  date_to?: string
  sender?: string
} = {}): Promise<CaseList> {
  const { data } = await api.get<CaseList>('/quarantine', { params })
  return data
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
