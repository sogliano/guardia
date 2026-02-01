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
import type { CostBreakdownPoint } from '@/types/monitoring'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps<{
  data: CostBreakdownPoint[]
}>()

const MODEL_COLORS: Record<string, string> = {
  'gpt-4.1': '#00D4FF',
  'gpt-4.1-mini': '#F97316',
  'gpt-4o': '#3B82F6',
  'gpt-4o-mini': '#22C55E',
}

const totalCost = computed(() => {
  const sum = props.data.reduce((acc, d) => acc + d.cost, 0)
  return sum.toFixed(2)
})

const chartData = computed(() => {
  const dates = [...new Set(props.data.map((d) => d.date))].sort()
  const models = [...new Set(props.data.map((d) => d.model))]
  const byDateModel = new Map<string, number>()
  for (const d of props.data) {
    byDateModel.set(`${d.date}|${d.model}`, d.cost)
  }

  return {
    labels: dates.map((d) => {
      const dt = new Date(d)
      return dt.toLocaleDateString('en-US', { weekday: 'short' })
    }),
    datasets: models.map((model) => ({
      label: model,
      data: dates.map((date) => byDateModel.get(`${date}|${model}`) ?? 0),
      borderColor: MODEL_COLORS[model] || '#6B7280',
      backgroundColor: (MODEL_COLORS[model] || '#6B7280') + '18',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 2,
    })),
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      align: 'start' as const,
      labels: {
        color: '#9CA3AF',
        boxWidth: 8,
        boxHeight: 8,
        usePointStyle: true,
        pointStyle: 'circle',
        font: { size: 11 },
      },
    },
    tooltip: {
      backgroundColor: '#1F2937',
      titleColor: '#F9FAFB',
      bodyColor: '#F9FAFB',
      borderColor: '#374151',
      borderWidth: 1,
      cornerRadius: 6,
      callbacks: {
        label: (ctx: { dataset: { label?: string }; parsed: { y: number | null } }) =>
          `${ctx.dataset.label ?? ''}: $${(ctx.parsed.y ?? 0).toFixed(3)}`,
      },
    },
  },
  interaction: { intersect: false, mode: 'index' as const },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#6B7280', font: { size: 11 } },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: {
        color: '#6B7280',
        font: { size: 11 },
        stepSize: 0.005,
        callback: (v: number | string) => `$${Number(v).toFixed(2)}`,
      },
      beginAtZero: true,
    },
  },
}
</script>

<template>
  <div class="card">
    <div class="header">
      <h3 class="section-title">Cost Breakdown</h3>
      <span class="total">Total: ${{ totalCost }}</span>
    </div>
    <div v-if="data.length" class="chart-area">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No cost data available</div>
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
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-title {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.total {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: #22C55E;
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
