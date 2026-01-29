export type UserRole = 'administrator' | 'analyst' | 'auditor'

export interface User {
  id: string
  clerk_id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  last_login_at: string | null
  created_at: string
}
