<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { ChartDataPoint } from '@/types/dashboard'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  data: ChartDataPoint[]
}>()

const riskColors: Record<string, string> = {
  low: '#22C55E',
  medium: '#F59E0B',
  high: '#F97316',
  critical: '#EF4444',
}

const total = computed(() => props.data.reduce((sum, d) => sum + d.value, 0) || 1)

const chartData = computed(() => ({
  labels: props.data.map((d) => d.label),
  datasets: [
    {
      data: props.data.map((d) => d.value),
      backgroundColor: props.data.map(
        (d) => riskColors[d.label.toLowerCase()] ?? '#6B7280'
      ),
      borderWidth: 0,
      hoverOffset: 4,
    },
  ],
}))

const riskOrder = ['low', 'medium', 'high', 'critical']

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '62%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1F2937',
      titleColor: '#F9FAFB',
      bodyColor: '#F9FAFB',
      borderColor: '#374151',
      borderWidth: 1,
      cornerRadius: 6,
      padding: { top: 6, bottom: 6, left: 10, right: 10 },
      bodyFont: { size: 13, weight: '500' as const },
      displayColors: false,
      callbacks: {
        title: () => '',
        label: (ctx: { label: string; parsed: number }) => {
          const pct = Math.round((ctx.parsed / total.value) * 100)
          return `${ctx.label}: ${ctx.parsed} (${pct}%)`
        },
      },
    },
  },
}))

const legendItems = computed(() => {
  const items = props.data.map((d) => ({
    label: d.label,
    value: d.value,
    color: riskColors[d.label.toLowerCase()] ?? '#6B7280',
    order: riskOrder.indexOf(d.label.toLowerCase()),
  }))
  items.sort((a, b) => a.order - b.order)
  return items
})
</script>

<template>
  <div class="risk-distribution">
    <h3 class="section-title">Risk Distribution</h3>

    <div v-if="data.length" class="chart-wrap">
      <div class="chart-container">
        <Doughnut :data="chartData" :options="chartOptions" />
        <div class="chart-center">
          <span class="chart-center-value">{{ total }}</span>
          <span class="chart-center-label">cases</span>
        </div>
      </div>
      <div class="legend">
        <div v-for="item in legendItems" :key="item.label" class="legend-item">
          <span class="legend-dot" :style="{ background: item.color }" />
          <span class="legend-text">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">No risk data available</div>
  </div>
</template>

<style scoped>
.risk-distribution {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.chart-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.chart-container {
  position: relative;
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.chart-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.chart-center-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.chart-center-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}

.legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-text {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: capitalize;
}

.legend-pct {
  font-size: 12px;
  font-weight: 600;
}

.empty-state {
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
