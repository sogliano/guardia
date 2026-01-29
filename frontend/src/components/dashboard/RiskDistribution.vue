<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
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

const viewMode = ref<'bars' | 'pie'>('bars')
const barsAnimated = ref(false)

function triggerBarsAnimation() {
  barsAnimated.value = false
  nextTick(() => {
    requestAnimationFrame(() => { barsAnimated.value = true })
  })
}

watch(viewMode, (v) => { if (v === 'bars') triggerBarsAnimation() }, { immediate: true })

const riskColors: Record<string, string> = {
  low: '#22C55E',
  medium: '#F59E0B',
  high: '#F97316',
  critical: '#EF4444',
}

const riskLabels: Record<string, string> = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
  critical: 'Critical',
}

const total = computed(() => props.data.reduce((sum, d) => sum + d.value, 0) || 1)

const riskOrder = ['low', 'medium', 'high', 'critical']

const barItems = computed(() => {
  const items = props.data.map((d) => {
    const key = d.label.toLowerCase()
    const pct = Math.round((d.value / total.value) * 100)
    return {
      key,
      label: riskLabels[key] ?? d.label,
      value: d.value,
      pct,
      color: riskColors[key] ?? '#6B7280',
      order: riskOrder.indexOf(key),
    }
  })
  items.sort((a, b) => a.order - b.order)
  return items
})

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
    <div class="section-header">
      <h3 class="section-title">Risk Distribution</h3>
      <div class="view-toggle">
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'bars' }"
          @click="viewMode = 'bars'"
        >
          <span class="material-symbols-rounded toggle-icon">bar_chart</span>
        </button>
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'pie' }"
          @click="viewMode = 'pie'"
        >
          <span class="material-symbols-rounded toggle-icon">pie_chart</span>
        </button>
      </div>
    </div>

    <template v-if="data.length">
      <div class="view-content">
      <!-- Bar View -->
      <div v-if="viewMode === 'bars'" class="bars-view">
        <div v-for="item in barItems" :key="item.key" class="bar-row">
          <div class="bar-label">
            <span class="bar-label-text" :style="{ color: item.color }">{{ item.label }}</span>
            <span class="bar-label-pct" :style="{ color: item.color }">{{ item.value }} ({{ item.pct }}%)</span>
          </div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{ width: barsAnimated ? item.pct + '%' : '0%', background: item.color }"
            />
          </div>
        </div>

        <!-- Stacked bar -->
        <div class="stacked-section">
          <span class="stacked-label">Overall Distribution</span>
          <div class="stacked-track">
            <div
              v-for="item in barItems"
              :key="'s-' + item.key"
              class="stacked-segment"
              :style="{ width: barsAnimated ? item.pct + '%' : '0%', background: item.color }"
            />
          </div>
          <div class="stacked-legend">
            <span
              v-for="item in barItems"
              :key="'l-' + item.key"
              class="stacked-legend-item"
              :style="{ color: item.color }"
            >
              <span class="stacked-legend-dot" :style="{ background: item.color }" />
              {{ item.pct }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Pie View -->
      <div v-else class="chart-wrap">
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
      </div>
    </template>
    <div v-else class="empty-state">No risk data available</div>
  </div>
</template>

<style scoped>
.risk-distribution {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.risk-distribution:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.view-toggle {
  display: flex;
  background: var(--bg-inset);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--border-radius-xs);
  transition: background 0.15s;
}

.toggle-btn.active {
  background: var(--accent-cyan-muted);
}

.toggle-icon {
  font-size: 16px;
  color: var(--text-muted);
}

.toggle-btn.active .toggle-icon {
  color: var(--accent-cyan);
}

.view-content {
  min-height: 240px;
  display: flex;
  flex-direction: column;
}

/* ── Bar View ── */
.bars-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-label-text {
  font-size: 12px;
  font-weight: normal;
}

.bar-label-pct {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
}

.bar-track {
  width: 100%;
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.stacked-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.stacked-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 0.3px;
}

.stacked-track {
  display: flex;
  width: 100%;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
}

.stacked-segment {
  height: 100%;
  transition: width 0.4s ease;
}

.stacked-legend {
  display: flex;
  gap: 12px;
}

.stacked-legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
}

.stacked-legend-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

/* ── Pie View ── */
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
  font-family: var(--font-mono);
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

.empty-state {
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
