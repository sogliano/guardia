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
import ErrorState from '@/components/common/ErrorState.vue'
import IngestEmailModal from '@/components/common/IngestEmailModal.vue'
import ScoreAnalysisTab from '@/components/monitoring/ScoreAnalysisTab.vue'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'
import LoadingState from '@/components/common/LoadingState.vue'
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

function openIngestModal() {
  showIngestModal.value = true
}

async function onIngested() {
  await store.fetchMonitoring()
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
  { key: 'score-analysis', label: 'Score Analysis' },
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
    <IngestEmailModal
      v-if="showIngestModal"
      @close="showIngestModal = false"
      @ingested="onIngested"
    />

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
    <LoadingState v-if="store.loading" message="Loading monitoring data..." />

    <!-- Error -->
    <ErrorState v-else-if="store.error" :message="store.error" :onRetry="() => store.fetchMonitoring()" />

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

    <!-- Score Analysis Tab Content -->
    <template v-else-if="store.activeTab === 'score-analysis'">
      <ScoreAnalysisTab />
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

@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row,
  .dual-row {
    grid-template-columns: 1fr;
  }
}


</style>
