<script setup lang="ts">
import { computed } from 'vue'
import type { PipelineHealthStats } from '@/types/dashboard'

const props = defineProps<{
  health: PipelineHealthStats | null
}>()

const stageNames: Record<string, string> = {
  heuristic: 'Heuristic Engine',
  ml: 'ML Classifier',
  llm: 'LLM Explainer',
}

const stages = computed(() => {
  if (!props.health) return []
  return Object.entries(props.health.stage_avg_ms).map(([key, avgMs]) => ({
    name: stageNames[key] ?? key,
    detail: `Avg ${avgMs.toFixed(1)}ms`,
    color: avgMs < 5000 ? '#22C55E' : avgMs < 10000 ? '#F59E0B' : '#EF4444',
  }))
})

const overallStatus = computed(() => {
  if (!props.health) return null
  const rate = props.health.success_rate
  return {
    label: rate >= 0.95 ? 'Healthy' : rate >= 0.8 ? 'Degraded' : 'Unhealthy',
    color: rate >= 0.95 ? '#22C55E' : rate >= 0.8 ? '#F59E0B' : '#EF4444',
    rate: (rate * 100).toFixed(1),
    avgMs: props.health.avg_duration_ms.toFixed(0),
  }
})
</script>

<template>
  <div class="pipeline-health">
    <h3 class="section-title">Pipeline Health</h3>

    <template v-if="overallStatus">
      <div class="overall-row">
        <div class="status-dot" :style="{ background: overallStatus.color }" />
        <span class="overall-text" :style="{ color: overallStatus.color }">
          {{ overallStatus.label }} · {{ overallStatus.rate }}% success · Avg {{ overallStatus.avgMs }}ms
        </span>
      </div>

      <div class="stages">
        <div v-for="s in stages" :key="s.name" class="stage-item">
          <div class="status-dot" :style="{ background: s.color }" />
          <div class="stage-info">
            <span class="stage-name">{{ s.name }}</span>
            <span class="stage-detail" :style="{ color: s.color }">{{ s.detail }}</span>
          </div>
        </div>
      </div>
    </template>
    <div v-else class="empty-state">No pipeline data available</div>
  </div>
</template>

<style scoped>
.pipeline-health {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 380px;
  flex-shrink: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.overall-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: var(--border-radius-sm);
}

.overall-text {
  font-size: 12px;
  font-weight: 500;
}

.stages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: var(--border-radius-sm);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.stage-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.stage-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.stage-detail {
  font-size: 11px;
}

.empty-state {
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
