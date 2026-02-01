<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { formatTimeAgo, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg } from '@/utils/colors'
import { RISK_OPTIONS, ACTION_OPTIONS, DATE_RANGE_OPTIONS, dateRangeToParams } from '@/constants/filterOptions'
import type { Case } from '@/types/case'

const router = useRouter()
const store = useCasesStore()

const searchQuery = ref('')
const filterRisk = ref<string | undefined>()
const filterAction = ref<string | undefined>()
const filterDateRange = ref<string | undefined>()

const hasActiveFilters = computed(() => {
  return searchQuery.value || filterRisk.value || filterAction.value || filterDateRange.value
})

function clearFilters() {
  searchQuery.value = ''
  filterRisk.value = undefined
  filterAction.value = undefined
  filterDateRange.value = undefined
}

const cases = computed(() => {
  let base = store.quarantineAndBlockedCases
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    base = base.filter(c =>
      (c.email_subject ?? '').toLowerCase().includes(q) ||
      (c.email_sender ?? '').toLowerCase().includes(q) ||
      String(c.case_number ?? '').includes(q)
    )
  }
  if (filterRisk.value) {
    base = base.filter(c => c.risk_level?.toLowerCase() === filterRisk.value!.toLowerCase())
  }
  if (filterAction.value) {
    base = base.filter(c => c.verdict?.toLowerCase() === filterAction.value!.toLowerCase())
  }
  if (filterDateRange.value) {
    const params = dateRangeToParams(filterDateRange.value)
    if (params.date_from) {
      base = base.filter(c => (c.email_received_at ?? c.created_at) >= params.date_from!)
    }
  }
  return base
})

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

    <div v-else class="quarantine-content">
      <div class="filter-bar">
        <div class="search-input-wrapper">
          <span class="material-symbols-rounded search-icon">search</span>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="Search subjects, senders, IDs..."
          />
        </div>
        <select v-model="filterRisk" class="filter-select">
          <option :value="undefined">Risk Level</option>
          <option v-for="opt in RISK_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
        </select>
        <select v-model="filterAction" class="filter-select">
          <option :value="undefined">Action</option>
          <option v-for="opt in ACTION_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
        </select>
        <select v-model="filterDateRange" class="filter-select">
          <option :value="undefined">Date Range</option>
          <option v-for="opt in DATE_RANGE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <a v-if="hasActiveFilters" href="#" class="clear-link" @click.prevent="clearFilters">Clear Filters</a>
        <span class="results-count">{{ cases.length }} cases</span>
      </div>
    <div class="table-card">
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
  </div>
</template>

<style scoped>
.quarantine-queue {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quarantine-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
