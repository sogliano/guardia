// ── Alert Rules ──────────────────────────────────────────────

export type AlertChannel = 'email' | 'slack'
export type AlertDeliveryStatus = 'pending' | 'delivered' | 'failed'

export interface AlertRule {
  id: string
  name: string
  description: string | null
  severity: string
  conditions: Record<string, unknown>
  channels: string[]
  is_active: boolean
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface AlertRuleCreate {
  name: string
  description?: string
  severity: string
  conditions?: Record<string, unknown>
  channels?: string[]
  is_active?: boolean
}

export interface AlertRuleUpdate {
  name?: string
  description?: string
  severity?: string
  conditions?: Record<string, unknown>
  channels?: string[]
  is_active?: boolean
}

// ── Alert Events ─────────────────────────────────────────────

export interface AlertEvent {
  id: string
  alert_rule_id: string
  case_id: string | null
  severity: string
  channel: string
  delivery_status: AlertDeliveryStatus
  trigger_info: Record<string, unknown>
  delivered_at: string | null
  created_at: string
}

export interface AlertEventList {
  items: AlertEvent[]
  total: number
  page: number
  size: number
}
