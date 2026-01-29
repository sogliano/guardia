export interface Email {
  id: string
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
  ingested_at: string
  created_at: string
  risk_level: string | null
  verdict: string | null
  final_score: number | null
}

export interface EmailList {
  items: Email[]
  total: number
  page: number
  size: number
}

export interface EmailIngest {
  message_id: string
  sender_email: string
  sender_name?: string
  reply_to?: string
  recipient_email: string
  recipients_cc?: string[]
  subject?: string
  body_text?: string
  body_html?: string
  headers?: Record<string, unknown>
  urls?: unknown[]
  attachments?: unknown[]
  auth_results?: Record<string, unknown>
  received_at?: string
}
