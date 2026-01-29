import api from './api'
import type { Setting, SettingUpdate } from '@/types/setting'

export async function fetchSettings(): Promise<Setting[]> {
  const { data } = await api.get<Setting[]>('/settings')
  return data
}

export async function fetchSetting(key: string): Promise<Setting> {
  const { data } = await api.get<Setting>(`/settings/${key}`)
  return data
}

export async function updateSetting(key: string, body: SettingUpdate): Promise<Setting> {
  const { data } = await api.put<Setting>(`/settings/${key}`, body)
  return data
}
