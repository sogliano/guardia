<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import type { VerdictTrendPoint } from '@/types/dashboard'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps<{
  data: VerdictTrendPoint[]
}>()

const singlePoint = computed(() => props.data.length === 1)

const chartData = computed(() => ({
  labels: props.data.map((d) => d.date),
  datasets: [
    {
      label: 'Blocked',
      data: props.data.map((d) => d.block),
      borderColor: '#EF4444',
      backgroundColor: 'rgba(239, 68, 68, 0.15)',
      fill: true,
      tension: 0.3,
      pointRadius: singlePoint.value ? 4 : 0,
      pointHoverRadius: 4,
    },
    {
      label: 'Quarantined',
      data: props.data.map((d) => d.quarantine),
      borderColor: '#F97316',
      backgroundColor: 'rgba(249, 115, 22, 0.15)',
      fill: true,
      tension: 0.3,
      pointRadius: singlePoint.value ? 4 : 0,
      pointHoverRadius: 4,
    },
    {
      label: 'Warned',
      data: props.data.map((d) => d.warn),
      borderColor: '#F59E0B',
      backgroundColor: 'rgba(245, 158, 11, 0.15)',
      fill: true,
      tension: 0.3,
      pointRadius: singlePoint.value ? 4 : 0,
      pointHoverRadius: 4,
    },
    {
      label: 'Allowed',
      data: props.data.map((d) => d.allow),
      borderColor: '#22C55E',
      backgroundColor: 'rgba(34, 197, 94, 0.15)',
      fill: true,
      tension: 0.3,
      pointRadius: singlePoint.value ? 4 : 0,
      pointHoverRadius: 4,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: {
        color: '#9CA3AF',
        font: { size: 11 },
        boxWidth: 8,
        boxHeight: 8,
        usePointStyle: true,
        pointStyle: 'circle',
        padding: 16,
      },
    },
    tooltip: {
      backgroundColor: '#1F2937',
      titleColor: '#F9FAFB',
      bodyColor: '#F9FAFB',
      borderColor: '#374151',
      borderWidth: 1,
      cornerRadius: 6,
      padding: { top: 8, bottom: 8, left: 12, right: 12 },
    },
  },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      ticks: { color: '#6B7280', font: { size: 10 }, maxTicksLimit: 10 },
    },
    y: {
      stacked: true,
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#6B7280', font: { size: 11 } },
      beginAtZero: true,
    },
  },
}
</script>

<template>
  <div class="verdict-timeline">
    <h3 class="section-title">Verdict Timeline</h3>
    <div v-if="data.length" class="chart-area">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No verdict trend data available</div>
  </div>
</template>

<style scoped>
.verdict-timeline {
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
