<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip } from 'chart.js'
import type { ScoreAgreement as ScoreAgreementType } from '@/types/monitoring'

ChartJS.register(ArcElement, Tooltip)

const props = defineProps<{
  data: ScoreAgreementType | null
  title?: string
}>()

const chartData = computed(() => {
  const d = props.data
  if (!d || d.total === 0) return null
  return {
    labels: ['Agree', 'Minor diff', 'Major divergence'],
    datasets: [
      {
        data: [d.agree_pct, d.minor_diff_pct, d.major_divergence_pct],
        backgroundColor: ['#22C55E', '#3B82F6', '#F97316'],
        borderWidth: 0,
        cutout: '70%',
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1F2937',
      titleColor: '#F9FAFB',
      bodyColor: '#F9FAFB',
      borderColor: '#374151',
      borderWidth: 1,
      cornerRadius: 6,
      callbacks: {
        label: (ctx: { label: string; parsed: number }) => `${ctx.label}: ${ctx.parsed}%`,
      },
    },
  },
}

const legendItems = computed(() => {
  if (!props.data) return []
  return [
    { label: `Agree (<0.15 diff)`, pct: props.data.agree_pct, color: '#22C55E' },
    { label: `Minor diff (0.15-0.30)`, pct: props.data.minor_diff_pct, color: '#3B82F6' },
    { label: `Major divergence (>0.30)`, pct: props.data.major_divergence_pct, color: '#F97316' },
  ]
})
</script>

<template>
  <div class="card">
    <h3 class="section-title">{{ title || 'Score Agreement (LLM vs Pipeline)' }}</h3>
    <div v-if="chartData" class="content">
      <div class="chart-wrapper">
        <Doughnut :data="chartData" :options="chartOptions" />
        <div class="center-label">
          <span class="pct">{{ data?.agree_pct ?? 0 }}%</span>
        </div>
      </div>
      <div class="legend">
        <div v-for="item in legendItems" :key="item.label" class="legend-item">
          <span class="dot" :style="{ background: item.color }" />
          <span class="legend-text">{{ item.label }} &mdash; {{ item.pct }}%</span>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">No agreement data available</div>
  </div>
</template>

<style scoped>
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.card:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}
.section-title {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.chart-wrapper {
  position: relative;
  width: 160px;
  height: 160px;
  flex-shrink: 0;
}
.center-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.pct {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 700;
  color: #22C55E;
}
.legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-text {
  font-size: 12px;
  color: var(--text-secondary);
}
.summary {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
  text-align: center;
}
.empty-state {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
