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
