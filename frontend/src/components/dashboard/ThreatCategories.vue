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
import type { ThreatCategoryCount } from '@/types/dashboard'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps<{
  data: ThreatCategoryCount[]
}>()

const categoryColors: Record<string, string> = {
  phishing: '#EF4444',
  bec: '#F97316',
  malware: '#DC2626',
  spam: '#F59E0B',
  impersonation: '#8B5CF6',
  credential_harvesting: '#EC4899',
  social_engineering: '#6366F1',
  clean: '#22C55E',
}

const sorted = computed(() =>
  [...props.data].sort((a, b) => b.count - a.count)
)

const chartData = computed(() => ({
  labels: sorted.value.map((d) => formatLabel(d.category)),
  datasets: [
    {
      data: sorted.value.map((d) => d.count),
      backgroundColor: sorted.value.map(
        (d) => categoryColors[d.category] ?? '#6B7280'
      ),
      borderRadius: 3,
      barThickness: 18,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
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
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#6B7280', font: { size: 11 } },
    },
    y: {
      grid: { display: false },
      ticks: { color: '#9CA3AF', font: { size: 12 } },
    },
  },
}

function formatLabel(cat: string): string {
  return cat
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<template>
  <div class="threat-categories">
    <h3 class="section-title">Threat Categories</h3>
    <div v-if="data.length" class="chart-area">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty-state">No category data available</div>
  </div>
</template>

<style scoped>
.threat-categories {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.threat-categories:hover {
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
