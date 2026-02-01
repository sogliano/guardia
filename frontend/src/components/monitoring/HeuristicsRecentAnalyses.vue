<script setup lang="ts">
import type { RecentHeuristicsAnalysis } from '@/types/monitoring'

defineProps<{
  data: RecentHeuristicsAnalysis[]
}>()

function formatTime(time: string): string {
  const dt = new Date(time)
  return dt.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatLatency(ms: number | null): string {
  if (ms === null) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`
}

function formatScore(score: number | null): string {
  return score !== null ? score.toFixed(2) : '—'
}

function formatRules(rules: string[]): string {
  if (!rules || rules.length === 0) return '—'
  return rules.join(', ')
}
</script>

<template>
  <div class="card">
    <h3 class="section-title">Recent Heuristic Analyses</h3>
    <div v-if="data.length" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>TIME</th>
            <th>CASE</th>
            <th>SENDER</th>
            <th>SCORE</th>
            <th>FINAL SCORE</th>
            <th>TRIGGERED RULES</th>
            <th>LATENCY</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data" :key="row.time">
            <td class="time">{{ formatTime(row.time) }}</td>
            <td class="case-number">{{ row.case_number ?? '—' }}</td>
            <td class="sender">{{ row.sender ?? '—' }}</td>
            <td class="score">{{ formatScore(row.heuristic_score) }}</td>
            <td class="score">{{ formatScore(row.final_score) }}</td>
            <td class="rules">{{ formatRules(row.triggered_rules) }}</td>
            <td class="latency">{{ formatLatency(row.latency_ms) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="empty-state">No recent heuristic analyses</div>
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
.table-wrapper {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
thead th {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  letter-spacing: 0.5px;
}
tbody td {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}
tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}
.time {
  color: var(--text-muted);
  font-size: 12px;
}
.case-number {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--text-primary);
}
.sender {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.score {
  font-family: var(--font-mono);
  font-weight: 500;
}
.rules {
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
  color: var(--text-muted);
}
.latency {
  font-family: var(--font-mono);
  font-size: 12px;
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
