<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { TopRulePoint } from '@/types/monitoring'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps<{
  data: TopRulePoint[]
}>()

const chartData = computed(() => ({
  labels: props.data.map((d) => d.rule_name),
  datasets: [
    {
      label: 'Triggered Count',
      data: props.data.map((d) => d.count),
      backgroundColor: '#A78BFA',
      borderRadius: 4,
      borderWidth: 0,
    },
  ],
}))

const chartOptions = {
  indexAxis: 'y' as const,
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
        label: (ctx: { parsed: { x: number | null } }) => `${ctx.parsed.x ?? 0} times`,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#6B7280', font: { size: 11 } },
      beginAtZero: true,
    },
    y: {
      grid: { display: false },
      ticks: {
        color: '#6B7280',
        font: { size: 11 },
        autoSkip: false,
      },
    },
  },
}
</script>

<template>
  <div class="card">
    <h3 class="section-title">Top Triggered Rules</h3>
    <div v-if="data.length" class="chart-area">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No triggered rules data available</div>
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
  height: 300px;
}
.empty-state {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
