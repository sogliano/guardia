<script setup lang="ts">
import { computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import type { RecentCaseItem } from '@/types/dashboard'

const props = defineProps<{
  cases: RecentCaseItem[]
}>()

function scoreColor(score: number | null): string {
  if (score === null) return '#6B7280'
  if (score >= 0.8) return '#EF4444'
  if (score >= 0.6) return '#F97316'
  if (score >= 0.3) return '#F59E0B'
  return '#22C55E'
}

function verdictColor(verdict: string | null): string {
  if (!verdict) return '#6B7280'
  const map: Record<string, string> = {
    blocked: '#EF4444',
    quarantined: '#F97316',
    warned: '#F59E0B',
    allowed: '#22C55E',
  }
  return map[verdict] ?? '#6B7280'
}

const rows = computed(() =>
  props.cases.map((c) => ({
    ...c,
    timeAgo: formatDistanceToNow(new Date(c.created_at), { addSuffix: true }),
    scoreDisplay: c.score !== null ? Math.round(c.score * 100) : '—',
    sColor: scoreColor(c.score),
    vColor: verdictColor(c.verdict),
    verdictLabel: c.verdict?.toUpperCase() ?? '—',
  }))
)
</script>

<template>
  <div class="recent-cases">
    <h3 class="section-title">Recent Critical Cases</h3>

    <div class="cases-header">
      <span class="col-header" style="width: 70px">Time</span>
      <span class="col-header" style="flex: 1">Subject</span>
      <span class="col-header" style="width: 130px">Sender</span>
      <span class="col-header" style="width: 50px">Score</span>
      <span class="col-header" style="width: 80px">Action</span>
    </div>

    <template v-if="rows.length">
      <div v-for="r in rows" :key="r.id" class="case-row">
        <span class="col-time">{{ r.timeAgo }}</span>
        <span class="col-subject">{{ r.subject ?? '(no subject)' }}</span>
        <span class="col-sender">{{ r.sender }}</span>
        <span class="col-score">
          <span class="score-badge" :style="{ color: r.sColor, background: r.sColor + '33' }">
            {{ r.scoreDisplay }}
          </span>
        </span>
        <span class="col-action">
          <span class="action-badge" :style="{ color: r.vColor, background: r.vColor + '33' }">
            {{ r.verdictLabel }}
          </span>
        </span>
      </div>
    </template>
    <div v-else class="empty-state">No recent cases</div>
  </div>
</template>

<style scoped>
.recent-cases {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.cases-header {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.col-header {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.case-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.col-time {
  width: 70px;
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.col-subject {
  flex: 1;
  font-size: 12px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-sender {
  width: 130px;
  font-size: 11px;
  color: var(--text-secondary);
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-score {
  width: 50px;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.score-badge {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: var(--border-radius-xs);
}

.col-action {
  width: 80px;
  flex-shrink: 0;
}

.action-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--border-radius-xs);
}

.empty-state {
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
