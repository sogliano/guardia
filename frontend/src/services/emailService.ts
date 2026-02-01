import api from './api'
import type { Email, EmailList } from '@/types/email'

export async function fetchEmails(params: {
  page?: number
  size?: number
  sender?: string
  search?: string
  date_from?: string
  date_to?: string
  risk_level?: string
} = {}): Promise<EmailList> {
  const { data } = await api.get<EmailList>('/emails', { params })
  return data
}

export async function fetchEmail(id: string): Promise<Email> {
  const { data } = await api.get<Email>(`/emails/${id}`)
  return data
}

export interface EmailIngestPayload {
  message_id: string
  sender_email: string
  sender_name: string | null
  reply_to: string | null
  recipient_email: string
  recipients_cc: string[]
  subject: string | null
  body_text: string | null
  body_html: string | null
  headers: Record<string, unknown>
  urls: unknown[]
  attachments: unknown[]
  auth_results: Record<string, unknown>
  received_at: string | null
}

export async function ingestEmail(payload: EmailIngestPayload): Promise<Email> {
  const { data } = await api.post<Email>('/emails/ingest', payload)
  return data
}
