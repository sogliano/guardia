<script setup lang="ts">
defineProps<{
  icon?: string
  iconColor?: string
  label: string
  value: string | number
  trend?: string
  trendColor?: string
  trendIcon?: string
  valueColor?: string
  details?: { text: string; color: string }[]
  badgeDetails?: boolean
  badgeFullText?: boolean
}>()

function extractNumber(text: string): string {
  const match = text.match(/^[\d,.]+/)
  return match ? match[0] : text
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
</script>

<template>
  <div class="stats-card">
    <div v-if="icon" class="card-icon-wrap" :style="{ background: hexToRgba(iconColor ?? '#6B7280', 0.12) }">
      <span class="material-symbols-rounded" :style="{ color: iconColor ?? 'var(--text-muted)' }">{{ icon }}</span>
    </div>
    <div class="card-content">
      <p class="card-label">{{ label }}</p>
      <p class="card-value" :style="valueColor ? { color: valueColor } : {}">{{ value }}</p>
      <div v-if="trend" class="card-trend">
        <span v-if="trendIcon" class="material-symbols-rounded trend-icon" :style="{ color: trendColor }">{{ trendIcon }}</span>
        <span class="trend-text" :style="{ color: trendColor }">{{ trend }}</span>
      </div>
      <div v-if="details?.length && badgeDetails" class="card-details">
        <span
          v-for="(d, i) in details"
          :key="i"
          class="detail-badge"
          :style="{ background: hexToRgba(d.color, 0.15), color: d.color }"
          :data-tooltip="badgeFullText ? undefined : d.text"
        >{{ badgeFullText ? d.text : extractNumber(d.text) }}</span>
      </div>
      <div v-else-if="details?.length" class="card-details-text">
        <template v-for="(d, i) in details" :key="i">
          <span v-if="i > 0" class="detail-sep">&middot;</span>
          <span class="detail-item" :style="{ color: d.color }">{{ d.text }}</span>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.stats-card:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}

.card-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon-wrap .material-symbols-rounded {
  font-size: 20px;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.card-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.card-value {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
}

.card-trend {
  display: flex;
  align-items: center;
  gap: 4px;
}

.trend-icon {
  font-size: 14px;
}

.trend-text {
  font-size: 12px;
}

.card-details {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 2px;
}

.card-details-text {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  overflow: hidden;
  margin-top: 2px;
}

.detail-sep {
  font-size: 11px;
  color: var(--text-dim);
}

.detail-item {
  font-size: 11px;
}

.detail-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--border-radius-xs);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  cursor: default;
}

.detail-badge::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: #1F2937;
  color: #F9FAFB;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  border-radius: 4px;
  border: 1px solid #374151;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
}

.detail-badge:hover::after {
  opacity: 1;
}
</style>
