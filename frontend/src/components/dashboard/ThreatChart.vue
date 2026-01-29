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

function barColor(value: number): string {
  if (value >= 20) return '#EF44444D'
  if (value >= 10) return '#F59E0B4D'
  return '#22C55E33'
}

const chartData = computed(() => ({
  labels: props.data.map((d) => d.label),
  datasets: [
    {
      label: 'Threats',
      data: props.data.map((d) => d.value),
      backgroundColor: props.data.map((d) => barColor(d.value)),
      borderRadius: { topLeft: 2, topRight: 2 },
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
      bodyColor: '#9CA3AF',
      borderColor: '#374151',
      borderWidth: 1,
      cornerRadius: 4,
    },
  },
  scales: {
    x: {
      display: false,
      grid: { display: false },
    },
    y: {
      display: false,
      grid: { display: false },
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
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
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
