import api from './api'
import type {
  PolicyEntry,
  PolicyEntryCreate,
  PolicyEntryList,
  CustomRule,
  CustomRuleCreate,
  CustomRuleUpdate,
} from '@/types/policy'

// ── Policy Entries ───────────────────────────────────────────

export async function fetchPolicyEntries(params: {
  page?: number
  size?: number
  list_type?: string
} = {}): Promise<PolicyEntryList> {
  const { data } = await api.get<PolicyEntryList>('/policies/entries', { params })
  return data
}

export async function createPolicyEntry(body: PolicyEntryCreate): Promise<PolicyEntry> {
  const { data } = await api.post<PolicyEntry>('/policies/entries', body)
  return data
}

export async function updatePolicyEntry(id: string, body: { is_active?: boolean }): Promise<PolicyEntry> {
  const { data } = await api.put<PolicyEntry>(`/policies/entries/${id}`, body)
  return data
}

export async function deletePolicyEntry(id: string): Promise<void> {
  await api.delete(`/policies/entries/${id}`)
}

// ── Custom Rules ─────────────────────────────────────────────

export async function fetchCustomRules(): Promise<CustomRule[]> {
  const { data } = await api.get<CustomRule[]>('/policies/rules')
  return data
}

export async function createCustomRule(body: CustomRuleCreate): Promise<CustomRule> {
  const { data } = await api.post<CustomRule>('/policies/rules', body)
  return data
}

export async function updateCustomRule(id: string, body: CustomRuleUpdate): Promise<CustomRule> {
  const { data } = await api.put<CustomRule>(`/policies/rules/${id}`, body)
  return data
}

export async function deleteCustomRule(id: string): Promise<void> {
  await api.delete(`/policies/rules/${id}`)
}
