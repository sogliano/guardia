<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'
import type { ChartDataPoint } from '@/types/dashboard'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps<{
  data: ChartDataPoint[]
}>()

function barBg(value: number): string {
  if (value >= 20) return 'rgba(239, 68, 68, 0.35)'
  if (value >= 10) return 'rgba(245, 158, 11, 0.30)'
  return 'rgba(34, 197, 94, 0.25)'
}

function barBorder(value: number): string {
  if (value >= 20) return 'rgba(239, 68, 68, 0.7)'
  if (value >= 10) return 'rgba(245, 158, 11, 0.6)'
  return 'rgba(34, 197, 94, 0.5)'
}

function formatLabel(label: string): string {
  // "2026-01-23" → "Jan 23"
  try {
    const d = new Date(label + 'T00:00:00')
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return label
  }
}

const chartData = computed(() => ({
  labels: props.data.map((d) => formatLabel(d.label)),
  datasets: [
    {
      label: 'Threats',
      data: props.data.map((d) => d.value),
      backgroundColor: props.data.map((d) => barBg(d.value)),
      borderColor: props.data.map((d) => barBorder(d.value)),
      borderWidth: 1,
      borderRadius: { topLeft: 3, topRight: 3 },
      borderSkipped: 'bottom' as const,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#111827',
      titleFont: { family: "'JetBrains Mono', monospace", size: 12, weight: '600' as const },
      bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
      titleColor: '#F9FAFB',
      bodyColor: '#9CA3AF',
      borderColor: '#374151',
      borderWidth: 1,
      cornerRadius: 4,
      padding: 10,
      displayColors: true,
      boxWidth: 8,
      boxHeight: 8,
      boxPadding: 4,
      callbacks: {
        label: (ctx: { parsed: { y: number } }) => ` ${ctx.parsed.y} cases`,
      },
    },
  },
  scales: {
    x: {
      display: true,
      grid: { display: false },
      ticks: {
        color: 'rgba(148, 163, 184, 0.6)',
        font: { family: "'JetBrains Mono', monospace", size: 10 },
        padding: 4,
      },
      border: { display: false },
    },
    y: {
      display: true,
      beginAtZero: true,
      grid: {
        color: 'rgba(148, 163, 184, 0.08)',
        lineWidth: 1,
      },
      ticks: {
        color: 'rgba(148, 163, 184, 0.5)',
        font: { family: "'JetBrains Mono', monospace", size: 10 },
        padding: 8,
        stepSize: 2,
        callback: (value: number) => value % 2 === 0 ? value : '',
      },
      border: { display: false },
    },
  },
}
</script>

<template>
  <div class="threat-chart">
    <h3 class="chart-title">Threat Trend (Last 30 days)</h3>
    <div v-if="data.length" class="chart-area">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No trend data available</div>
  </div>
</template>

<style scoped>
.threat-chart {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.threat-chart:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}

.chart-title {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-area {
  height: 220px;
}

.empty-state {
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
