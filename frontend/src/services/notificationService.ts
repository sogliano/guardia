import api from './api'
import type { NotificationList } from '@/types/notification'

export async function fetchNotifications(params: {
  page?: number
  size?: number
  is_read?: boolean
} = {}): Promise<NotificationList> {
  const { data } = await api.get<NotificationList>('/notifications', { params })
  return data
}

export async function markNotificationRead(id: string): Promise<void> {
  await api.put(`/notifications/${id}/read`)
}

export async function markAllRead(): Promise<{ updated: number }> {
  const { data } = await api.post<{ updated: number }>('/notifications/mark-all-read')
  return data
}

export async function fetchUnreadCount(): Promise<number> {
  const { data } = await api.get<{ unread_count: number }>('/notifications/unread-count')
  return data.unread_count
}
