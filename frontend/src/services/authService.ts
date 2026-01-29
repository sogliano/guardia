import api from './api'
import type { User } from '@/types/auth'

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}
