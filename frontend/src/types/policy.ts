// ── Policy Entries (Whitelist / Blacklist) ────────────────────

export type PolicyListType = 'whitelist' | 'blacklist'
export type PolicyEntryType = 'domain' | 'email' | 'ip'

export interface PolicyEntry {
  id: string
  list_type: PolicyListType
  entry_type: PolicyEntryType
  value: string
  is_active: boolean
  added_by: string | null
  created_at: string
  updated_at: string
}

export interface PolicyEntryCreate {
  list_type: PolicyListType
  entry_type: PolicyEntryType
  value: string
  is_active?: boolean
}

export interface PolicyEntryList {
  items: PolicyEntry[]
  total: number
  page: number
  size: number
}

// ── Custom Rules ─────────────────────────────────────────────

export interface CustomRule {
  id: string
  name: string
  description: string | null
  conditions: Record<string, unknown>
  action: string
  is_active: boolean
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface CustomRuleCreate {
  name: string
  description?: string
  conditions?: Record<string, unknown>
  action: string
  is_active?: boolean
}

export interface CustomRuleUpdate {
  name?: string
  description?: string
  conditions?: Record<string, unknown>
  action?: string
  is_active?: boolean
}
