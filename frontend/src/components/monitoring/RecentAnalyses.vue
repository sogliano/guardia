<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns'
import { scoreColor } from '@/utils/colors'
import type { RecentLLMAnalysis } from '@/types/monitoring'

defineProps<{
  data: RecentLLMAnalysis[]
  totalCalls?: number
}>()

function formatTime(iso: string): string {
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true })
  } catch {
    return iso
  }
}

function statusClass(status: string): string {
  if (status === 'success') return 'badge-success'
  if (status === 'timeout') return 'badge-warning'
  return 'badge-error'
}

function formatTokens(n: number | null): string {
  if (n == null) return '\u2014'
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)
}

function formatLatency(ms: number | null): string {
  if (ms == null) return '\u2014'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

function formatScore(score: number | null): string {
  if (score == null) return '\u2014'
  return score.toFixed(2)
}

function scoreDiff(llm: number | null, final: number | null): string {
  if (llm == null || final == null) return '\u2014'
  const diff = llm - final
  if (Math.abs(diff) < 0.01) return '±0.00'
  return diff > 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)
}

function diffColor(llm: number | null, final: number | null): string {
  if (llm == null || final == null) return 'var(--text-muted)'
  const diff = Math.abs(llm - final)
  if (diff < 0.15) return '#22C55E'
  if (diff < 0.30) return '#3B82F6'
  return '#F97316'
}

function formatCategory(cat: string | null | undefined): string {
  if (!cat) return '\u2014'
  return cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}
</script>

<template>
  <div class="card">
    <div class="header">
      <h3 class="section-title">Recent LLM Analyses</h3>
      <span v-if="totalCalls" class="total">{{ totalCalls.toLocaleString() }} total</span>
    </div>
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>TIME</th>
            <th>CASE ID</th>
            <th>SENDER</th>
            <th class="num">LLM</th>
            <th class="num">FINAL</th>
            <th class="num">DIFF</th>
            <th>CATEGORY</th>
            <th class="num">TOKENS</th>
            <th class="num">LATENCY</th>
            <th>MODEL</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in data" :key="i">
            <td class="mono dim">{{ formatTime(row.time) }}</td>
            <td class="mono">
              <span v-if="row.case_number" class="case-id">#{{ row.case_number }}</span>
              <span v-else class="dim">\u2014</span>
            </td>
            <td class="mono sender">{{ row.sender ?? '\u2014' }}</td>
            <td class="num mono" :style="{ color: scoreColor(row.llm_score) }">
              {{ formatScore(row.llm_score) }}
            </td>
            <td class="num mono" :style="{ color: scoreColor(row.final_score) }">
              {{ formatScore(row.final_score) }}
            </td>
            <td class="num mono" :style="{ color: diffColor(row.llm_score, row.final_score) }">
              {{ scoreDiff(row.llm_score, row.final_score) }}
            </td>
            <td class="category">{{ formatCategory(row.threat_category) }}</td>
            <td class="num mono dim">{{ formatTokens(row.tokens) }}</td>
            <td class="num mono dim">{{ formatLatency(row.latency_ms) }}</td>
            <td class="mono dim model">{{ row.model ?? '\u2014' }}</td>
            <td>
              <span :class="['badge', statusClass(row.status)]">{{ row.status }}</span>
            </td>
          </tr>
          <tr v-if="!data.length">
            <td colspan="11" class="empty">No recent analyses</td>
          </tr>
        </tbody>
      </table>
    </div>
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
  font-size: 12px;
  color: var(--text-muted);
}
.table-wrapper {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-inset);
}
th.num {
  text-align: right;
}
td {
  font-size: 12px;
  color: var(--text-primary);
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}
td.num {
  text-align: right;
  font-weight: 600;
}
td.mono {
  font-family: var(--font-mono);
}
td.dim {
  color: var(--text-muted);
}
td.empty {
  text-align: center;
  color: var(--text-muted);
  padding: 32px 12px;
}
.case-id {
  color: #00D4FF;
  font-weight: 600;
}
.sender {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.category {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.3px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.model {
  font-size: 11px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.badge {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: capitalize;
}
.badge-success {
  color: #22C55E;
  background: rgba(34, 197, 94, 0.12);
}
.badge-warning {
  color: #F97316;
  background: rgba(249, 115, 22, 0.12);
}
.badge-error {
  color: #EF4444;
  background: rgba(239, 68, 68, 0.12);
}
</style>
