<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  trend?: string
  trendColor?: string
  trendIcon?: string
  valueColor?: string
  details?: { text: string; color: string }[]
}>()
</script>

<template>
  <div class="stats-card">
    <p class="card-label">{{ label }}</p>
    <p class="card-value" :style="valueColor ? { color: valueColor } : {}">{{ value }}</p>
    <div v-if="trend" class="card-trend">
      <span v-if="trendIcon" class="material-symbols-rounded trend-icon" :style="{ color: trendColor }">{{ trendIcon }}</span>
      <span class="trend-text" :style="{ color: trendColor }">{{ trend }}</span>
    </div>
    <div v-if="details?.length" class="card-details">
      <template v-for="(d, i) in details" :key="i">
        <span v-if="i > 0" class="detail-sep">&middot;</span>
        <span class="detail-item" :style="{ color: d.color }">{{ d.text }}</span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.stats-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
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
  gap: 8px;
  flex-wrap: wrap;
}

.detail-sep {
  font-size: 11px;
  color: var(--text-dim);
}

.detail-item {
  font-size: 11px;
}
</style>
