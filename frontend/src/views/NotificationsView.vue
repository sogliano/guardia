<script setup lang="ts">
import { onMounted } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDate } from '@/utils/formatters'

const store = useNotificationsStore()

function severityClass(sev: string): string {
  const map: Record<string, string> = { info: 'badge-info', warning: 'badge-warn', critical: 'badge-critical' }
  return map[sev] ?? 'badge-info'
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    critical_threat: 'Critical Threat',
    quarantine_pending: 'Quarantine Pending',
    false_positive: 'False Positive',
    pipeline_health: 'Pipeline Health',
    system: 'System',
  }
  return map[type] ?? type
}

onMounted(() => {
  store.fetchNotifications()
})
</script>

<template>
  <div class="notifications">
    <div class="page-header">
      <div class="header-row">
        <div>
          <h2>Notifications</h2>
          <span class="subtitle">{{ store.unreadCount }} unread notification{{ store.unreadCount !== 1 ? 's' : '' }}</span>
        </div>
        <button
          v-if="store.unreadCount > 0"
          class="btn btn-secondary"
          @click="store.markAllRead()"
        >
          <span class="material-symbols-rounded btn-icon">done_all</span>
          Mark All Read
        </button>
      </div>
    </div>

    <div v-if="store.loading && !store.items.length" class="loading-container">
      <span class="spinner"></span>
    </div>

    <div v-else-if="store.error" class="error-message">
      <p>{{ store.error }}</p>
      <button class="btn btn-primary" @click="store.fetchNotifications()">
        <span class="material-symbols-rounded btn-icon">refresh</span>
        Retry
      </button>
    </div>

    <div v-else-if="!store.items.length" class="empty-state">
      <span class="material-symbols-rounded empty-icon">notifications_off</span>
      <p>No notifications</p>
    </div>

    <div v-else class="notification-list">
      <div
        v-for="n in store.items"
        :key="n.id"
        class="notification-item"
        :class="{ unread: !n.is_read }"
        @click="!n.is_read && store.markRead(n.id)"
      >
        <div class="notification-left">
          <div class="notification-header">
            <span class="pill-badge" :class="severityClass(n.severity)">{{ typeLabel(n.type) }}</span>
            <span v-if="!n.is_read" class="unread-dot"></span>
          </div>
          <h4 class="notification-title">{{ n.title }}</h4>
          <p v-if="n.message" class="notification-message">{{ n.message }}</p>
        </div>
        <div class="notification-right">
          <span class="notification-date">{{ formatDate(n.created_at) }}</span>
          <button
            v-if="!n.is_read"
            class="btn-icon-only"
            @click.stop="store.markRead(n.id)"
          >
            <span class="material-symbols-rounded">check</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notifications {
  padding: var(--space-lg);
}

.page-header {
  margin-bottom: var(--space-lg);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-header h2 {
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--border-radius-sm);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.3px;
}

.btn-primary {
  background: var(--accent-cyan);
  color: var(--bg-primary);
}

.btn-primary:hover {
  filter: brightness(1.15);
}

.btn-secondary {
  background: rgba(0, 212, 255, 0.08);
  color: var(--accent-cyan);
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(0, 212, 255, 0.15);
}

.btn-icon {
  font-size: 16px;
}

.btn-icon-only {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--border-radius-sm);
  background: rgba(0, 212, 255, 0.08);
  color: var(--accent-cyan);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon-only:hover {
  background: rgba(0, 212, 255, 0.18);
}

.btn-icon-only .material-symbols-rounded {
  font-size: 16px;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 48px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 212, 255, 0.15);
  border-top-color: var(--accent-cyan);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  text-align: center;
  padding: 48px;
  color: var(--color-block);
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.4;
  display: block;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.notification-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: background-color 0.15s;
}

.notification-item:hover {
  background: var(--bg-hover);
}

.notification-item.unread {
  border-left: 3px solid var(--accent-cyan);
  background: rgba(0, 212, 255, 0.03);
}

.notification-left {
  flex: 1;
}

.notification-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.pill-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 10px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-info {
  background: rgba(0, 212, 255, 0.12);
  color: var(--accent-cyan);
}

.badge-warn {
  background: rgba(255, 170, 0, 0.12);
  color: var(--color-warn);
}

.badge-critical {
  background: rgba(255, 60, 60, 0.12);
  color: var(--color-block);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-cyan);
  flex-shrink: 0;
}

.notification-title {
  margin: 0 0 4px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.notification-message {
  margin: 0;
  color: var(--text-muted);
  font-size: 12px;
  font-family: var(--font-mono);
}

.notification-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.notification-date {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}
</style>
