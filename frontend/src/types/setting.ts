export interface Setting {
  id: string
  key: string
  value: unknown
  updated_by: string | null
  created_at: string
  updated_at: string
}

export interface SettingUpdate {
  value: unknown
}
