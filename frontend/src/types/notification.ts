export type NotificationType =
  | 'critical_threat'
  | 'quarantine_pending'
  | 'false_positive'
  | 'pipeline_health'
  | 'system'

export type NotificationSeverity = 'info' | 'warning' | 'critical'

export interface Notification {
  id: string
  user_id: string
  type: NotificationType
  severity: NotificationSeverity
  title: string
  message: string | null
  is_read: boolean
  reference_id: string | null
  reference_type: string | null
  created_at: string
}

export interface NotificationList {
  items: Notification[]
  total: number
  unread_count: number
}
