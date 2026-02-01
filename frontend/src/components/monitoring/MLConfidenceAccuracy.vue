<script setup lang="ts">
import { computed } from 'vue'
import { Scatter } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { ConfidenceAccuracyPoint } from '@/types/monitoring'

ChartJS.register(LinearScale, PointElement, Tooltip, Legend)

const props = defineProps<{
  data: ConfidenceAccuracyPoint[]
}>()

const chartData = computed(() => ({
  datasets: [
    {
      label: 'Confidence vs Accuracy',
      data: props.data.map((d) => ({ x: d.confidence, y: d.accuracy })),
      backgroundColor: props.data.map((d) => {
        if (d.accuracy >= 0.85) return '#22C55E'
        if (d.accuracy >= 0.7) return '#FBBF24'
        return '#EF4444'
      }),
      borderColor: 'rgba(255, 255, 255, 0.2)',
      borderWidth: 1,
      pointRadius: 4,
      pointHoverRadius: 6,
    },
  ],
}))

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
        label: (ctx: { parsed: { x: number | null; y: number | null } }) =>
          `Confidence: ${((ctx.parsed.x ?? 0) * 100).toFixed(0)}% | Accuracy: ${((ctx.parsed.y ?? 0) * 100).toFixed(0)}%`,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: {
        color: '#6B7280',
        font: { size: 11 },
        callback: (v: number | string) => `${(Number(v) * 100).toFixed(0)}%`,
      },
      title: {
        display: true,
        text: 'Confidence',
        color: '#9CA3AF',
        font: { size: 12, weight: 500 as const },
      },
      min: 0,
      max: 1,
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: {
        color: '#6B7280',
        font: { size: 11 },
        callback: (v: number | string) => `${(Number(v) * 100).toFixed(0)}%`,
      },
      title: {
        display: true,
        text: 'Accuracy',
        color: '#9CA3AF',
        font: { size: 12, weight: 500 as const },
      },
      min: 0,
      max: 1,
    },
  },
}
</script>

<template>
  <div class="card">
    <h3 class="section-title">Confidence vs Accuracy</h3>
    <div v-if="data.length" class="chart-area">
      <Scatter :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No confidence data available</div>
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
