<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns'
import type { ActiveAlertItem } from '@/types/dashboard'

const props = defineProps<{
  alerts: ActiveAlertItem[]
}>()

function severityColor(severity: string): string {
  const map: Record<string, string> = {
    critical: '#EF4444',
    high: '#F97316',
    medium: '#F59E0B',
    low: '#22C55E',
  }
  return map[severity] ?? '#F59E0B'
}
</script>

<template>
  <div v-if="alerts.length" class="active-alerts">
    <div class="alert-header">
      <div class="alert-title">
        <span class="material-symbols-rounded alert-icon">warning</span>
        <span class="alert-title-text">Active Alerts ({{ alerts.length }})</span>
      </div>
    </div>

    <div v-for="a in alerts" :key="a.id" class="alert-row">
      <div class="alert-dot" :style="{ background: severityColor(a.severity) }" />
      <div class="alert-content">
        <span class="alert-rule">{{ a.rule_name }}</span>
        <span class="alert-text">{{ a.message }}</span>
      </div>
      <span class="alert-time">{{ formatDistanceToNow(new Date(a.created_at), { addSuffix: true }) }}</span>
    </div>
  </div>
</template>

<style scoped>
.active-alerts {
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.19);
  border-radius: var(--border-radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.active-alerts:hover {
  border-color: rgba(245, 158, 11, 0.3);
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.08);
}

.alert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.alert-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-icon {
  font-size: 16px;
  color: #F59E0B;
  font-variation-settings: 'wght' 300;
}

.alert-title-text {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: #F59E0B;
}

.alert-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.alert-dot {
  width: 6px;
  height: 6px;
  border-radius: 3px;
  flex-shrink: 0;
  margin-top: 5px;
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alert-rule {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.alert-text {
  font-size: 12px;
  color: var(--text-primary);
  line-height: 1.4;
}

.alert-time {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
