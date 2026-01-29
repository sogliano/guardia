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
import annotationPlugin from 'chartjs-plugin-annotation'
import type { ScoreBucket } from '@/types/dashboard'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, annotationPlugin)

const props = defineProps<{
  data: ScoreBucket[]
}>()

function bucketColor(range: string): string {
  const start = parseFloat(range.split('-')[0])
  if (start >= 0.8) return '#EF4444'
  if (start >= 0.6) return '#F97316'
  if (start >= 0.3) return '#F59E0B'
  return '#22C55E'
}

const chartData = computed(() => ({
  labels: props.data.map((d) => d.range),
  datasets: [
    {
      data: props.data.map((d) => d.count),
      backgroundColor: props.data.map((d) => bucketColor(d.range)),
      borderRadius: 2,
    },
  ],
}))

const chartOptions = computed(() => ({
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
      padding: { top: 6, bottom: 6, left: 10, right: 10 },
      bodyFont: { size: 13, weight: '500' as const },
      displayColors: false,
      callbacks: {
        label: (ctx: { parsed: { y: number } }) => `${ctx.parsed.y} emails`,
      },
    },
    annotation: {
      annotations: {
        warnLine: {
          type: 'line' as const,
          xMin: 2.5,
          xMax: 2.5,
          borderColor: '#F59E0B',
          borderWidth: 1.5,
          borderDash: [4, 4],
          label: {
            display: true,
            content: 'Warn',
            position: 'start' as const,
            color: '#F59E0B',
            font: { size: 10 },
            backgroundColor: 'transparent',
          },
        },
        quarantineLine: {
          type: 'line' as const,
          xMin: 7.5,
          xMax: 7.5,
          borderColor: '#EF4444',
          borderWidth: 1.5,
          borderDash: [4, 4],
          label: {
            display: true,
            content: 'Quarantine',
            position: 'start' as const,
            color: '#EF4444',
            font: { size: 10 },
            backgroundColor: 'transparent',
          },
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#6B7280', font: { size: 10 } },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#6B7280', font: { size: 11 } },
      beginAtZero: true,
    },
  },
}))
</script>

<template>
  <div class="score-distribution">
    <h3 class="section-title">Score Distribution</h3>
    <div v-if="data.length" class="chart-area">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No score data available</div>
  </div>
</template>

<style scoped>
.score-distribution {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.score-distribution:hover {
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
  height: 200px;
}

.empty-state {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
