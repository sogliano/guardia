<script setup lang="ts">
import { onMounted } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const store = useNotificationsStore()

function severityColor(sev: string): string {
  const map: Record<string, string> = { info: 'info', warning: 'warn', critical: 'danger' }
  return map[sev] ?? 'info'
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

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
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
        <Button
          v-if="store.unreadCount > 0"
          label="Mark All Read"
          icon="pi pi-check-circle"
          severity="secondary"
          text
          @click="store.markAllRead()"
        />
      </div>
    </div>

    <div v-if="store.loading && !store.items.length" class="loading-container">
      <ProgressSpinner />
    </div>

    <div v-else-if="store.error" class="error-message">
      <p>{{ store.error }}</p>
      <Button label="Retry" icon="pi pi-refresh" @click="store.fetchNotifications()" />
    </div>

    <div v-else-if="!store.items.length" class="empty-state">
      <i class="pi pi-bell-slash empty-icon"></i>
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
            <Tag :value="typeLabel(n.type)" :severity="severityColor(n.severity)" />
            <span v-if="!n.is_read" class="unread-dot"></span>
          </div>
          <h4 class="notification-title">{{ n.title }}</h4>
          <p v-if="n.message" class="notification-message">{{ n.message }}</p>
        </div>
        <div class="notification-right">
          <span class="notification-date">{{ formatDate(n.created_at) }}</span>
          <Button
            v-if="!n.is_read"
            icon="pi pi-check"
            text
            size="small"
            @click.stop="store.markRead(n.id)"
          />
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
}

.subtitle {
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: var(--space-xl);
}

.error-message {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-block);
}

.empty-state {
  text-align: center;
  padding: var(--space-xl);
  color: var(--text-color-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--space-md);
  opacity: 0.4;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.notification-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-md);
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s;
  margin-bottom: var(--space-xs);
}

.notification-item:hover {
  background: var(--surface-hover);
}

.notification-item.unread {
  border-left: 3px solid var(--primary-color);
  background: color-mix(in srgb, var(--primary-color) 5%, var(--surface-card));
}

.notification-left {
  flex: 1;
}

.notification-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
}

.notification-title {
  margin: 0 0 4px 0;
  font-size: 0.95rem;
}

.notification-message {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 0.85rem;
}

.notification-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.notification-date {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
  white-space: nowrap;
}
</style>
