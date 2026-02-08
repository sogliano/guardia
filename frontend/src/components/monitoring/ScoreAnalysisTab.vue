<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { scoreColor } from '@/utils/colors'
import LoadingState from '@/components/common/LoadingState.vue'

interface ScoreMetrics {
  agreement_rate: number
  avg_std_dev: number
  correlation_heur_ml: number
  correlation_heur_llm: number
  correlation_ml_llm: number
  total_cases_analyzed: number
}

interface CaseScoreBreakdown {
  case_number: number
  email_sender: string
  email_received_at: string
  heuristic_score: number | null
  ml_score: number | null
  llm_score: number | null
  final_score: number
  std_dev: number
  agreement_level: 'high' | 'moderate' | 'low'
}

const router = useRouter()
const loading = ref(true)
const metrics = ref<ScoreMetrics | null>(null)
const cases = ref<CaseScoreBreakdown[]>([])

async function fetchScoreAnalysis() {
  loading.value = true
  try {
    const response = await api.get('/monitoring/score-analysis?limit=50')
    metrics.value = response.data.metrics
    cases.value = response.data.cases
  } catch (err) {
    console.error('Failed to fetch score analysis:', err)
  } finally {
    loading.value = false
  }
}

function agreementIcon(level: string): string {
  if (level === 'high') return 'check_circle'
  if (level === 'moderate') return 'warning'
  return 'cancel'
}

function agreementColor(level: string): string {
  if (level === 'high') return 'text-green-600'
  if (level === 'moderate') return 'text-yellow-600'
  return 'text-red-600'
}

function agreementLabel(level: string): string {
  if (level === 'high') return 'Alta concordancia'
  if (level === 'moderate') return 'Divergencia moderada'
  return 'Divergencia alta'
}

function formatScore(score: number | null): string {
  return score !== null ? score.toFixed(2) : 'N/A'
}

function truncateSender(sender: string): string {
  return sender.length > 30 ? sender.slice(0, 27) + '...' : sender
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

function goToCase(caseNumber: number) {
  router.push(`/cases/${caseNumber}`)
}

function getScoreTooltip(c: CaseScoreBreakdown): string {
  const heur = formatScore(c.heuristic_score)
  const ml = formatScore(c.ml_score)
  const llm = formatScore(c.llm_score)
  return `Final Score: ${c.final_score.toFixed(2)}\n\nCalculation:\n─────────────────\nHeuristic: ${heur} × 30% = ${(c.heuristic_score || 0) * 0.3}\nML:        ${ml} × 50% = ${(c.ml_score || 0) * 0.5}\nLLM:       ${llm} × 20% = ${(c.llm_score || 0) * 0.2}\n─────────────────\nFinal:              ${c.final_score.toFixed(3)}`
}

const metricsHealth = computed(() => {
  if (!metrics.value) return { color: '#6B7280', label: 'N/A' }
  const { agreement_rate, avg_std_dev } = metrics.value
  if (agreement_rate >= 85 && avg_std_dev < 0.1) {
    return { color: '#22C55E', label: 'Excelente concordancia', icon: 'check_circle' }
  }
  if (agreement_rate >= 70 && avg_std_dev <= 0.2) {
    return { color: '#FBBF24', label: 'Concordancia moderada', icon: 'warning' }
  }
  return { color: '#EF4444', label: 'Divergencia alta', icon: 'cancel' }
})

onMounted(() => {
  fetchScoreAnalysis()
})
</script>

<template>
  <div class="score-analysis-tab">
    <!-- Metrics Card -->
    <div v-if="!loading && metrics" class="metrics-card">
      <div class="metrics-header">
        <h3>Engine Agreement Metrics</h3>
        <div class="health-badge" :style="{ color: metricsHealth.color }">
          <span class="material-symbols-rounded">{{ metricsHealth.icon }}</span>
          {{ metricsHealth.label }}
        </div>
      </div>
      <div class="metrics-grid">
        <div class="metric">
          <span class="label">Agreement Rate:</span>
          <span class="value">{{ metrics.agreement_rate.toFixed(1) }}%</span>
        </div>
        <div class="metric">
          <span class="label">Avg Std Dev:</span>
          <span class="value">{{ metrics.avg_std_dev.toFixed(3) }}</span>
        </div>
        <div class="metric">
          <span class="label">Corr (Heur-ML):</span>
          <span class="value">{{ metrics.correlation_heur_ml.toFixed(2) }}</span>
        </div>
        <div class="metric">
          <span class="label">Corr (Heur-LLM):</span>
          <span class="value">{{ metrics.correlation_heur_llm.toFixed(2) }}</span>
        </div>
        <div class="metric">
          <span class="label">Corr (ML-LLM):</span>
          <span class="value">{{ metrics.correlation_ml_llm.toFixed(2) }}</span>
        </div>
        <div class="metric">
          <span class="label">Total Cases:</span>
          <span class="value">{{ metrics.total_cases_analyzed }}</span>
        </div>
      </div>
    </div>

    <!-- Cases Table -->
    <div v-if="!loading" class="cases-table-container">
      <h3>Detailed Score Breakdown (Last 50 Cases)</h3>
      <div class="table-wrapper">
        <table class="cases-table">
          <thead>
            <tr>
              <th>Case #</th>
              <th>Sender</th>
              <th>Date</th>
              <th>Heuristic</th>
              <th>ML</th>
              <th>LLM</th>
              <th>Final</th>
              <th>Agreement</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in cases" :key="c.case_number" @click="goToCase(c.case_number)">
              <td class="case-number">#{{ c.case_number }}</td>
              <td class="sender">{{ truncateSender(c.email_sender) }}</td>
              <td class="date">{{ formatTimeAgo(c.email_received_at) }}</td>
              <td>
                <span class="score-badge" :style="{ backgroundColor: scoreColor(c.heuristic_score) }">
                  {{ formatScore(c.heuristic_score) }}
                </span>
              </td>
              <td>
                <span class="score-badge" :style="{ backgroundColor: scoreColor(c.ml_score) }">
                  {{ formatScore(c.ml_score) }}
                </span>
              </td>
              <td>
                <span class="score-badge" :style="{ backgroundColor: scoreColor(c.llm_score) }">
                  {{ formatScore(c.llm_score) }}
                </span>
              </td>
              <td>
                <span
                  class="score-badge final"
                  :style="{ backgroundColor: scoreColor(c.final_score) }"
                  :title="getScoreTooltip(c)"
                >
                  {{ formatScore(c.final_score) }}
                </span>
              </td>
              <td>
                <span :class="agreementColor(c.agreement_level)" :title="agreementLabel(c.agreement_level)" class="agreement-icon material-symbols-rounded">
                  {{ agreementIcon(c.agreement_level) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="cases.length === 0" class="empty-state">
        No cases with complete scoring data available
      </div>
    </div>

    <LoadingState v-if="loading" message="Loading score analysis..." />
  </div>
</template>

<style scoped>
.score-analysis-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metrics-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.metrics-header h3 {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.health-badge {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric .label {
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric .value {
  font-size: 24px;
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-primary);
}

.cases-table-container {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cases-table-container h3 {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 16px 0;
}

.table-wrapper {
  overflow-x: auto;
}

.cases-table {
  width: 100%;
  border-collapse: collapse;
}

.cases-table th {
  text-align: left;
  padding: 12px;
  border-bottom: 2px solid var(--border-color);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cases-table td {
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
}

.cases-table tbody tr {
  cursor: pointer;
  transition: background 0.15s;
}

.cases-table tbody tr:hover {
  background: rgba(0, 212, 255, 0.04);
}

.case-number {
  font-weight: 700;
  color: var(--accent-cyan);
}

.sender {
  color: var(--text-secondary);
}

.date {
  color: var(--text-muted);
  font-size: 12px;
}

.score-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  font-weight: 600;
  font-size: 12px;
  min-width: 45px;
  text-align: center;
}

.score-badge.final {
  cursor: help;
}

.agreement-icon {
  font-size: 18px;
  font-weight: 700;
  cursor: help;
}

.text-green-600 {
  color: #22C55E;
}

.text-yellow-600 {
  color: #FBBF24;
}

.text-red-600 {
  color: #EF4444;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 13px;
}

@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
