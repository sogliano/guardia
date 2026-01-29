<script setup lang="ts">
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import ThreatChart from '@/components/dashboard/ThreatChart.vue'
import RiskDistribution from '@/components/dashboard/RiskDistribution.vue'
import RecentCases from '@/components/dashboard/RecentCases.vue'
import PipelineHealth from '@/components/dashboard/PipelineHealth.vue'
import ActiveAlerts from '@/components/dashboard/ActiveAlerts.vue'
import ThreatCategories from '@/components/dashboard/ThreatCategories.vue'
import VerdictTimeline from '@/components/dashboard/VerdictTimeline.vue'
import ScoreDistribution from '@/components/dashboard/ScoreDistribution.vue'
import TopSenders from '@/components/dashboard/TopSenders.vue'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'

const store = useDashboardStore()

onMounted(() => {
  store.fetchDashboard()
})
</script>

<template>
  <div class="dashboard">
    <GlobalFiltersBar />

    <!-- KPI Row -->
    <div class="kpi-row">
      <StatsCard
        icon="mail"
        icon-color="#9CA3AF"
        label="Emails Analyzed"
        :value="store.data?.stats.total_emails_analyzed?.toLocaleString() ?? '—'"
        :details="[
          { text: `${store.data?.stats.emails_today ?? 0} today`, color: '#6B7280' },
        ]"
      />
      <StatsCard
        icon="gpp_bad"
        icon-color="#EF4444"
        label="Threats Detected"
        :value="String((store.data?.stats.blocked_count ?? 0) + (store.data?.stats.quarantined_count ?? 0) + (store.data?.stats.warned_count ?? 0))"
        value-color="#EF4444"
        badge-details
        :details="[
          { text: `${store.data?.stats.blocked_count ?? 0} blocked`, color: '#EF4444' },
          { text: `${store.data?.stats.quarantined_count ?? 0} quarantined`, color: '#F97316' },
          { text: `${store.data?.stats.warned_count ?? 0} warned`, color: '#F59E0B' },
        ]"
      />
      <StatsCard
        icon="shield"
        icon-color="#F97316"
        label="Blocked / Quarantined"
        :value="String((store.data?.stats.blocked_count ?? 0) + (store.data?.stats.quarantined_count ?? 0))"
        value-color="#F97316"
        badge-details
        :details="[
          { text: `${store.data?.stats.blocked_count ?? 0} blocked`, color: '#EF4444' },
          { text: `${store.data?.stats.quarantined_count ?? 0} quarantined`, color: '#F97316' },
        ]"
      />
      <StatsCard
        icon="speed"
        icon-color="#00D4FF"
        label="Avg Response Time"
        :value="store.data?.pipeline_health ? `${(store.data.pipeline_health.avg_duration_ms / 1000).toFixed(1)}s` : '—'"
        value-color="#00D4FF"
        badge-details
        badge-full-text
        :details="store.data?.pipeline_health ? [
          { text: `Heuristic ${store.data.pipeline_health.stage_avg_ms?.heuristic?.toFixed(0) ?? '~5'}ms`, color: '#9CA3AF' },
          { text: `ML ${store.data.pipeline_health.stage_avg_ms?.ml?.toFixed(0) ?? '~18'}ms`, color: '#9CA3AF' },
          { text: `LLM ${store.data.pipeline_health.stage_avg_ms?.llm ? (store.data.pipeline_health.stage_avg_ms.llm / 1000).toFixed(1) + 's' : '~2s'}`, color: '#9CA3AF' },
        ] : []"
      />
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <ThreatChart :data="store.data?.daily_trend ?? []" />
      <RiskDistribution :data="store.data?.risk_distribution ?? []" />
    </div>

    <!-- Verdict Timeline (full width) -->
    <VerdictTimeline :data="store.data?.verdict_trend ?? []" />

    <!-- Threat Categories + Score Distribution -->
    <div class="dual-row">
      <ThreatCategories :data="store.data?.threat_categories ?? []" />
      <ScoreDistribution :data="store.data?.score_distribution ?? []" />
    </div>

    <!-- Cases + Pipeline Row -->
    <div class="bottom-row">
      <RecentCases :cases="store.data?.recent_cases ?? []" />
      <PipelineHealth :health="store.data?.pipeline_health ?? null" />
    </div>

    <!-- Top Senders -->
    <TopSenders :senders="store.data?.top_senders ?? []" />

    <!-- Active Alerts -->
    <ActiveAlerts :alerts="store.data?.active_alerts ?? []" />
  </div>
</template>

<style scoped>
.dashboard {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-x: hidden;
}

.kpi-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1.4fr;
  gap: 12px;
  min-width: 0;
}

.kpi-row > * {
  min-width: 0;
}

.charts-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
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

.bottom-row {
  display: flex;
  gap: 16px;
}

.bottom-row > :first-child {
  flex: 1;
  min-width: 0;
}

.bottom-row > :last-child {
  width: 380px;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row,
  .dual-row {
    grid-template-columns: 1fr;
  }
  .bottom-row {
    flex-direction: column;
  }
}
</style>
