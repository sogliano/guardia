import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Notification } from '@/types/notification'
import {
  fetchNotifications as fetchNotificationsApi,
  markNotificationRead,
  markAllRead as markAllReadApi,
  fetchUnreadCount,
} from '@/services/notificationService'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<Notification[]>([])
  const total = ref(0)
  const unreadCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchNotifications(isRead?: boolean) {
    loading.value = true
    error.value = null
    try {
      const result = await fetchNotificationsApi({ is_read: isRead })
      items.value = result.items
      total.value = result.total
      unreadCount.value = result.unread_count
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load notifications'
    } finally {
      loading.value = false
    }
  }

  async function markRead(id: string) {
    await markNotificationRead(id)
    const item = items.value.find((n) => n.id === id)
    if (item) item.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  async function markAllRead() {
    await markAllReadApi()
    items.value.forEach((n) => (n.is_read = true))
    unreadCount.value = 0
  }

  async function refreshUnreadCount() {
    unreadCount.value = await fetchUnreadCount()
  }

  return {
    items,
    total,
    unreadCount,
    loading,
    error,
    fetchNotifications,
    markRead,
    markAllRead,
    refreshUnreadCount,
  }
})
