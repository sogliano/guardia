<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useMonitoringStore } from '@/stores/monitoring'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import TokenUsageTrend from '@/components/monitoring/TokenUsageTrend.vue'
import LatencyDistribution from '@/components/monitoring/LatencyDistribution.vue'
import ScoreAgreement from '@/components/monitoring/ScoreAgreement.vue'
import CostBreakdown from '@/components/monitoring/CostBreakdown.vue'
import RecentAnalyses from '@/components/monitoring/RecentAnalyses.vue'
import MLScoreDistribution from '@/components/monitoring/MLScoreDistribution.vue'
import MLConfidenceAccuracy from '@/components/monitoring/MLConfidenceAccuracy.vue'
import MLLatencyTrend from '@/components/monitoring/MLLatencyTrend.vue'
import MLRecentAnalyses from '@/components/monitoring/MLRecentAnalyses.vue'
import HeuristicsScoreDistribution from '@/components/monitoring/HeuristicsScoreDistribution.vue'
import HeuristicsRecentAnalyses from '@/components/monitoring/HeuristicsRecentAnalyses.vue'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'
import { ingestEmail } from '@/services/emailService'
import type {
  HeuristicsMonitoringData,
  MLMonitoringData,
  MonitoringData,
} from '@/types/monitoring'

const store = useMonitoringStore()

const llmData = computed(() => store.data as MonitoringData | null)
const mlData = computed(() => store.data as MLMonitoringData | null)
const heuristicsData = computed(() => store.data as HeuristicsMonitoringData | null)

const showIngestModal = ref(false)
const ingesting = ref(false)
const ingestError = ref('')

const ingestForm = ref({
  message_id: '',
  sender_email: '',
  sender_name: '',
  recipient_email: '',
  subject: '',
  body_text: '',
})

function openIngestModal() {
  showIngestModal.value = true
  ingestError.value = ''
  ingestForm.value = {
    message_id: `test-${Date.now()}@guardia.local`,
    sender_email: '',
    sender_name: '',
    recipient_email: 'security@strikesecurity.io',
    subject: '',
    body_text: '',
  }
}

function closeIngestModal() {
  showIngestModal.value = false
}

async function submitIngest() {
  ingesting.value = true
  ingestError.value = ''
  try {
    await ingestEmail({
      message_id: ingestForm.value.message_id,
      sender_email: ingestForm.value.sender_email,
      sender_name: ingestForm.value.sender_name || null,
      reply_to: null,
      recipient_email: ingestForm.value.recipient_email,
      recipients_cc: [],
      subject: ingestForm.value.subject || null,
      body_text: ingestForm.value.body_text || null,
      body_html: null,
      headers: {},
      urls: [],
      attachments: [],
      auth_results: {},
      received_at: null,
    })
    closeIngestModal()
    await store.fetchMonitoring()
  } catch (err: any) {
    ingestError.value = err.response?.data?.detail || 'Failed to ingest email'
  } finally {
    ingesting.value = false
  }
}

onMounted(() => {
  store.fetchMonitoring()
})

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
  return String(n)
}

function formatLatency(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`
}

function trendPct(): string {
  const kpi = llmData.value?.kpi
  if (!kpi || kpi.prev_total_calls === 0) return ''
  const diff = ((kpi.total_calls - kpi.prev_total_calls) / kpi.prev_total_calls) * 100
  return `${diff > 0 ? '+' : ''}${diff.toFixed(1)}% vs previous`
}

const tabs = [
  { key: 'heuristics', label: 'Heuristics' },
  { key: 'ml', label: 'ML Classifier' },
  { key: 'llm', label: 'LLM Explainer' },
] as const
</script>

<template>
  <div class="monitoring">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Monitoring</h1>
        <p class="subtitle">Pipeline performance, costs, and quality metrics</p>
      </div>
      <div class="header-right">
        <button class="btn-primary" @click="openIngestModal">
          <span class="material-symbols-rounded btn-icon">upload</span>
          Ingest Email
        </button>
        <GlobalFiltersBar />
      </div>
    </div>

    <!-- Ingest Email Modal -->
    <div v-if="showIngestModal" class="modal-overlay" @click="closeIngestModal">
      <div class="modal-card" @click.stop>
        <div class="modal-header">
          <h2>Ingest Email</h2>
          <button class="close-btn" @click="closeIngestModal">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <form @submit.prevent="submitIngest" class="modal-body">
          <div class="form-group">
            <label>Message ID</label>
            <input v-model="ingestForm.message_id" type="text" required class="form-input" />
          </div>
          <div class="form-group">
            <label>Sender Email *</label>
            <input v-model="ingestForm.sender_email" type="email" required class="form-input" placeholder="attacker@example.com" />
          </div>
          <div class="form-group">
            <label>Sender Name</label>
            <input v-model="ingestForm.sender_name" type="text" class="form-input" placeholder="John Doe" />
          </div>
          <div class="form-group">
            <label>Recipient Email *</label>
            <input v-model="ingestForm.recipient_email" type="email" required class="form-input" />
          </div>
          <div class="form-group">
            <label>Subject</label>
            <input v-model="ingestForm.subject" type="text" class="form-input" placeholder="Urgent: Password Reset Required" />
          </div>
          <div class="form-group">
            <label>Body Text</label>
            <textarea v-model="ingestForm.body_text" class="form-textarea" rows="6" placeholder="Email body content..."></textarea>
          </div>
          <div v-if="ingestError" class="error-message">{{ ingestError }}</div>
          <div class="modal-footer">
            <button type="button" class="btn-outline" @click="closeIngestModal" :disabled="ingesting">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="ingesting">
              <span v-if="ingesting" class="material-symbols-rounded btn-icon spinning">progress_activity</span>
              <span v-else class="material-symbols-rounded btn-icon">upload</span>
              {{ ingesting ? 'Ingesting...' : 'Ingest Email' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', { active: store.activeTab === tab.key }]"
        @click="store.activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-state">Loading monitoring data...</div>

    <!-- Error -->
    <div v-else-if="store.error" class="error-state">{{ store.error }}</div>

    <!-- Heuristics Tab Content -->
    <template v-else-if="store.activeTab === 'heuristics'">
      <div class="kpi-row">
        <StatsCard
          icon="rule"
          icon-color="#A78BFA"
          label="Total Runs"
          :value="heuristicsData?.kpi?.total_runs.toLocaleString() ?? '—'"
          :trend="
            heuristicsData?.kpi?.prev_total_runs
              ? `${heuristicsData.kpi.total_runs > heuristicsData.kpi.prev_total_runs ? '+' : ''}${(
                  ((heuristicsData.kpi.total_runs - heuristicsData.kpi.prev_total_runs) /
                    heuristicsData.kpi.prev_total_runs) *
                  100
                ).toFixed(1)}% vs previous`
              : ''
          "
          trend-color="#22C55E"
        />
        <StatsCard
          icon="speed"
          icon-color="#22C55E"
          label="Avg Latency"
          :value="heuristicsData?.kpi ? `${Math.round(heuristicsData.kpi.avg_latency_ms)}ms` : '—'"
          badge-details
          :details="
            heuristicsData?.kpi
              ? [{ text: `P95: ${Math.round(heuristicsData.kpi.p95_latency_ms)}ms`, color: '#6B7280' }]
              : []
          "
        />
        <StatsCard
          icon="trending_up"
          icon-color="#F97316"
          label="High Score Rate"
          :value="heuristicsData?.kpi ? `${heuristicsData.kpi.high_score_rate}%` : '—'"
          badge-details
          :details="
            heuristicsData?.kpi
              ? [{ text: 'Score ≥ 0.6', color: '#6B7280' }]
              : []
          "
        />
        <StatsCard
          icon="trending_down"
          icon-color="#3B82F6"
          label="Zero Score Rate"
          :value="heuristicsData?.kpi ? `${heuristicsData.kpi.zero_score_rate}%` : '—'"
          badge-details
          :details="
            heuristicsData?.kpi
              ? [{ text: 'Missed by heuristics', color: '#6B7280' }]
              : []
          "
        />
      </div>

      <div class="dual-row">
        <ScoreAgreement :data="heuristicsData?.score_agreement ?? null" title="Score Agreement (Heuristic vs Pipeline)" />
        <HeuristicsScoreDistribution :data="heuristicsData?.score_distribution ?? []" />
      </div>

      <HeuristicsRecentAnalyses :data="heuristicsData?.recent_analyses ?? []" />
    </template>

    <!-- ML Tab Content -->
    <template v-else-if="store.activeTab === 'ml'">
      <div class="kpi-row">
        <StatsCard
          icon="psychology"
          icon-color="#3B82F6"
          label="Total ML Calls"
          :value="mlData?.kpi?.total_calls.toLocaleString() ?? '—'"
          :trend="
            mlData?.kpi?.prev_total_calls
              ? `${mlData.kpi.total_calls > mlData.kpi.prev_total_calls ? '+' : ''}${(
                  ((mlData.kpi.total_calls - mlData.kpi.prev_total_calls) / mlData.kpi.prev_total_calls) *
                  100
                ).toFixed(1)}% vs previous`
              : ''
          "
          trend-color="#22C55E"
        />
        <StatsCard
          icon="speed"
          icon-color="#22C55E"
          label="Avg Latency"
          :value="
            mlData?.kpi
              ? mlData.kpi.avg_latency_ms >= 1000
                ? `${(mlData.kpi.avg_latency_ms / 1000).toFixed(1)}s`
                : `${Math.round(mlData.kpi.avg_latency_ms)}ms`
              : '—'
          "
          badge-details
          :details="
            mlData?.kpi
              ? [
                  {
                    text: `P95: ${
                      mlData.kpi.p95_latency_ms >= 1000
                        ? `${(mlData.kpi.p95_latency_ms / 1000).toFixed(1)}s`
                        : `${Math.round(mlData.kpi.p95_latency_ms)}ms`
                    }`,
                    color: '#6B7280',
                  },
                ]
              : []
          "
        />
        <StatsCard
          icon="analytics"
          icon-color="#A78BFA"
          label="Avg Confidence"
          :value="mlData?.kpi ? `${(mlData.kpi.avg_confidence * 100).toFixed(0)}%` : '—'"
        />
        <StatsCard
          icon="error_outline"
          icon-color="#EF4444"
          label="Error Rate"
          :value="mlData?.kpi ? `${mlData.kpi.error_rate}%` : '—'"
          :value-color="
            mlData?.kpi
              ? mlData.kpi.error_rate === 0
                ? '#22C55E'
                : mlData.kpi.error_rate > 5
                ? '#EF4444'
                : '#F97316'
              : undefined
          "
          badge-details
          :details="
            mlData?.kpi
              ? [
                  {
                    text: `${mlData.kpi.error_count}/${mlData.kpi.total_calls}`,
                    color: '#6B7280',
                  },
                ]
              : []
          "
        />
      </div>

      <div class="charts-row">
        <MLScoreDistribution :data="mlData?.score_distribution ?? []" />
        <MLConfidenceAccuracy :data="mlData?.confidence_accuracy ?? []" />
      </div>

      <div class="dual-row">
        <MLLatencyTrend :data="mlData?.latency_trend ?? []" />
        <ScoreAgreement :data="mlData?.score_agreement ?? null" title="Score Agreement (ML vs Pipeline)" />
      </div>

      <MLRecentAnalyses :data="mlData?.recent_analyses ?? []" />
    </template>

    <!-- LLM Tab Content -->
    <template v-else-if="store.activeTab === 'llm'">
      <!-- KPI Row -->
      <div class="kpi-row">
        <StatsCard
          icon="smart_toy"
          icon-color="#00D4FF"
          label="Total LLM Calls"
          :value="llmData?.kpi?.total_calls.toLocaleString() ?? '—'"
          :trend="trendPct()"
          trend-color="#22C55E"
        />
        <StatsCard
          icon="speed"
          icon-color="#22C55E"
          label="Avg Latency"
          :value="llmData?.kpi ? formatLatency(llmData.kpi.avg_latency_ms) : '—'"
          badge-details
          :details="
            llmData?.kpi ? [{ text: `P95: ${formatLatency(llmData.kpi.p95_latency_ms)}`, color: '#6B7280' }] : []
          "
        />
        <StatsCard
          icon="token"
          icon-color="#3B82F6"
          label="Total Tokens"
          :value="llmData?.kpi ? formatTokens(llmData.kpi.total_tokens) : '—'"
          badge-details
          :details="llmData?.kpi ? [{ text: `Est. $${llmData.kpi.estimated_cost.toFixed(2)}`, color: '#6B7280' }] : []"
        />
        <StatsCard
          icon="error_outline"
          icon-color="#EF4444"
          label="Error Rate"
          :value="llmData?.kpi ? `${llmData.kpi.error_rate}%` : '—'"
          :value-color="
            llmData?.kpi
              ? llmData.kpi.error_rate === 0
                ? '#22C55E'
                : llmData.kpi.error_rate > 5
                ? '#EF4444'
                : '#F97316'
              : undefined
          "
          badge-details
          :details="
            llmData?.kpi
              ? [
                  {
                    text: `${llmData.kpi.error_count}/${llmData.kpi.total_calls}`,
                    color: '#6B7280',
                  },
                ]
              : []
          "
        />
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <TokenUsageTrend :data="llmData?.token_trend ?? []" />
        <LatencyDistribution :data="llmData?.latency_distribution ?? []" />
      </div>

      <!-- Second Row -->
      <div class="dual-row">
        <ScoreAgreement :data="llmData?.score_agreement ?? null" />
        <CostBreakdown :data="llmData?.cost_breakdown ?? []" />
      </div>

      <!-- Recent Analyses Table -->
      <RecentAnalyses :data="llmData?.recent_analyses ?? []" :total-calls="llmData?.kpi?.total_calls" />
    </template>
  </div>
</template>

<style scoped>
.monitoring {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-x: hidden;
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
  font-weight: 400;
}

.header-left {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 12px;
}

.tab-bar {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0;
}

.tab {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  background: none;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.2s, border-color 0.2s;
}

.tab:hover:not(.disabled) {
  color: var(--text-primary);
}

.tab.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
}

.tab.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  min-width: 0;
}

.kpi-row > * {
  min-width: 0;
}

.charts-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  min-width: 0;
}

.charts-row > * {
  min-width: 0;
}

.dual-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-width: 0;
}

.dual-row > * {
  min-width: 0;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 48px 0;
  font-size: 14px;
  color: var(--text-muted);
}

.error-state {
  color: #EF4444;
}

@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row,
  .dual-row {
    grid-template-columns: 1fr;
  }
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.close-btn .material-symbols-rounded {
  font-size: 20px;
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  background: var(--bg-inset);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #00D4FF;
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.error-message {
  padding: 10px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--border-radius);
  color: #EF4444;
  font-size: 12px;
  font-family: var(--font-mono);
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
