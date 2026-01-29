import api from './api'
import type { AlertRule, AlertRuleCreate, AlertRuleUpdate, AlertEventList } from '@/types/alert'

// ── Alert Rules ──────────────────────────────────────────────

export async function fetchAlertRules(params: {
  page?: number
  size?: number
} = {}): Promise<AlertRule[]> {
  const { data } = await api.get<AlertRule[]>('/alerts/rules', { params })
  return data
}

export async function createAlertRule(body: AlertRuleCreate): Promise<AlertRule> {
  const { data } = await api.post<AlertRule>('/alerts/rules', body)
  return data
}

export async function getAlertRule(id: string): Promise<AlertRule> {
  const { data } = await api.get<AlertRule>(`/alerts/rules/${id}`)
  return data
}

export async function updateAlertRule(id: string, body: AlertRuleUpdate): Promise<AlertRule> {
  const { data } = await api.put<AlertRule>(`/alerts/rules/${id}`, body)
  return data
}

export async function deleteAlertRule(id: string): Promise<void> {
  await api.delete(`/alerts/rules/${id}`)
}

// ── Alert Events ─────────────────────────────────────────────

export async function fetchAlertEvents(params: {
  page?: number
  size?: number
} = {}): Promise<AlertEventList> {
  const { data } = await api.get<AlertEventList>('/alerts/events', { params })
  return data
}
