<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { formatTimeAgo, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg } from '@/utils/colors'
import type { Case } from '@/types/case'

const router = useRouter()
const store = useCasesStore()

const cases = computed(() => store.quarantineAndBlockedCases)

type SortDir = 'asc' | 'desc'
const sortCol = ref<string | null>(null)
const sortDir = ref<SortDir>('asc')

const riskOrder: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 }

function getSortValue(c: Case, col: string): string | number {
  if (col === 'sender') return c.email_sender ?? ''
  if (col === 'subject') return c.email_subject ?? ''
  if (col === 'score') return c.final_score ?? -1
  if (col === 'risk') return riskOrder[c.risk_level ?? ''] ?? 0
  if (col === 'category') return c.threat_category ?? ''
  if (col === 'verdict') return c.verdict ?? ''
  if (col === 'received') return c.email_received_at ?? c.created_at ?? ''
  return ''
}

const sortedCases = computed(() => {
  if (!sortCol.value) return cases.value
  const sorted = [...cases.value].sort((a, b) => {
    const va = getSortValue(a, sortCol.value!)
    const vb = getSortValue(b, sortCol.value!)
    if (va < vb) return -1
    if (va > vb) return 1
    return 0
  })
  return sortDir.value === 'desc' ? sorted.reverse() : sorted
})

function toggleSort(col: string) {
  if (sortCol.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortCol.value = col
    sortDir.value = 'asc'
  }
}

function sortIcon(col: string): string {
  if (sortCol.value !== col) return 'unfold_more'
  return sortDir.value === 'asc' ? 'expand_less' : 'expand_more'
}

function formatCategory(cat: string): string {
  return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function openCase(id: string) {
  router.push({ name: 'case-detail', params: { id } })
}
</script>

<template>
  <div class="quarantine-queue">
    <div v-if="cases.length === 0" class="empty-tab">
      <span class="material-symbols-rounded empty-tab-icon">verified_user</span>
      <p>No quarantined or blocked emails</p>
      <span class="empty-tab-hint">All clear — no emails are waiting for review</span>
    </div>

    <div v-else class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th class="sortable-th" style="width: 220px" @click="toggleSort('sender')">
              SENDER <span class="material-symbols-rounded sort-icon">{{ sortIcon('sender') }}</span>
            </th>
            <th class="sortable-th" @click="toggleSort('subject')">
              SUBJECT <span class="material-symbols-rounded sort-icon">{{ sortIcon('subject') }}</span>
            </th>
            <th class="sortable-th" style="width: 70px" @click="toggleSort('score')">
              SCORE <span class="material-symbols-rounded sort-icon">{{ sortIcon('score') }}</span>
            </th>
            <th class="sortable-th" style="width: 90px" @click="toggleSort('risk')">
              RISK <span class="material-symbols-rounded sort-icon">{{ sortIcon('risk') }}</span>
            </th>
            <th class="sortable-th" style="width: 160px" @click="toggleSort('category')">
              CATEGORY <span class="material-symbols-rounded sort-icon">{{ sortIcon('category') }}</span>
            </th>
            <th class="sortable-th" style="width: 120px" @click="toggleSort('verdict')">
              VERDICT <span class="material-symbols-rounded sort-icon">{{ sortIcon('verdict') }}</span>
            </th>
            <th class="sortable-th" style="width: 100px" @click="toggleSort('received')">
              RECEIVED <span class="material-symbols-rounded sort-icon">{{ sortIcon('received') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in sortedCases"
            :key="c.id"
            class="case-row"
            @click="openCase(c.id)"
          >
            <td class="cell-sender">{{ c.email_sender ?? 'Unknown' }}</td>
            <td class="cell-subject">{{ c.email_subject ?? '(No Subject)' }}</td>
            <td>
              <span class="score-val" :style="{ color: scoreColor(c.final_score) }">
                {{ c.final_score !== null ? (c.final_score * 100).toFixed(0) + '%' : '—' }}
              </span>
            </td>
            <td>
              <span
                v-if="c.risk_level"
                class="pill-badge"
                :style="{ color: riskColor(c.risk_level), background: riskBg(c.risk_level) }"
              >{{ capitalize(c.risk_level) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span v-if="c.threat_category" class="cell-category">{{ formatCategory(c.threat_category) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span
                v-if="c.verdict"
                class="pill-badge"
                :style="{ color: actionColor(c.verdict), background: actionBg(c.verdict) }"
              >{{ capitalize(c.verdict) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="cell-date">{{ formatTimeAgo(c.email_received_at ?? c.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.quarantine-queue {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
