<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { resolveCase } from '@/services/caseService'
import type { Case } from '@/types/case'
import { formatDate, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg, statusColor, statusBg } from '@/utils/colors'
import { computePageNumbers } from '@/utils/pagination'
import { RISK_OPTIONS, ACTION_OPTIONS, STATUS_OPTIONS, DATE_RANGE_OPTIONS, dateRangeToParams } from '@/constants/filterOptions'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'

const router = useRouter()
const store = useCasesStore()

const searchQuery = ref('')
const filterRisk = ref<string | undefined>()
const filterAction = ref<string | undefined>()
const filterStatus = ref<string | undefined>()
const filterDateRange = ref<string | undefined>()

const naPage = ref(1)
const naPageSize = ref(10)
const allowingCaseId = ref<string | null>(null)
const blockingCaseId = ref<string | null>(null)

type SortDir = 'asc' | 'desc'
const naSortCol = ref<string | null>(null)
const naSortDir = ref<SortDir>('asc')
const sortCol = ref<string | null>(null)
const sortDir = ref<SortDir>('asc')

let searchTimer: ReturnType<typeof setTimeout> | null = null

const naTotalPages = computed(() => Math.ceil(needsActionCases.value.length / naPageSize.value))
const paginatedNeedsCases = computed(() => {
  const start = (naPage.value - 1) * naPageSize.value
  return sortedNeedsAction.value.slice(start, start + naPageSize.value)
})
const naStartItem = computed(() => (naPage.value - 1) * naPageSize.value + 1)
const naEndItem = computed(() => Math.min(naPage.value * naPageSize.value, needsActionCases.value.length))

const totalPages = computed(() => Math.ceil(store.total / store.size))
const startItem = computed(() => (store.page - 1) * store.size + 1)
const endItem = computed(() => Math.min(store.page * store.size, store.total))

const hasActiveFilters = computed(() => {
  return searchQuery.value || filterRisk.value || filterAction.value || filterStatus.value || filterDateRange.value
})

const pageNumbers = computed(() => computePageNumbers(store.page, totalPages.value))

// Overview computeds
const needsActionCases = computed(() =>
  store.cases.filter(c => c.status === 'analyzed' || c.status === 'quarantined')
)

const resolvedCount = computed(() => store.cases.filter(c => c.status === 'resolved').length)
const highRiskCount = computed(() => store.cases.filter(c => c.risk_level === 'high' || c.risk_level === 'critical').length)
const avgScore = computed(() => {
  const scored = store.cases.filter(c => c.final_score !== null)
  if (!scored.length) return null
  return scored.reduce((sum, c) => sum + (c.final_score ?? 0), 0) / scored.length
})

const riskOrder: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 }
const statusOrder: Record<string, number> = { quarantined: 4, analyzed: 3, analyzing: 2, pending: 1, resolved: 0 }

function getSortValue(c: Case, col: string): string | number {
  if (col === 'case_number') return c.case_number ?? 0
  if (col === 'received') return c.email_received_at ?? c.created_at ?? ''
  if (col === 'score') return c.final_score ?? -1
  if (col === 'risk') return riskOrder[c.risk_level ?? ''] ?? 0
  if (col === 'action') return c.verdict ?? ''
  if (col === 'status') return statusOrder[c.status ?? ''] ?? 0
  return ''
}

function sortCases<T extends Case>(list: T[], col: string | null, dir: SortDir): T[] {
  if (!col) return list
  const sorted = [...list].sort((a, b) => {
    const va = getSortValue(a, col)
    const vb = getSortValue(b, col)
    if (va < vb) return -1
    if (va > vb) return 1
    return 0
  })
  return dir === 'desc' ? sorted.reverse() : sorted
}

function toggleSort(table: 'na' | 'all', col: string) {
  const colRef = table === 'na' ? naSortCol : sortCol
  const dirRef = table === 'na' ? naSortDir : sortDir
  if (colRef.value === col) {
    dirRef.value = dirRef.value === 'asc' ? 'desc' : 'asc'
  } else {
    colRef.value = col
    dirRef.value = 'asc'
  }
}

function sortIcon(table: 'na' | 'all', col: string): string {
  const colRef = table === 'na' ? naSortCol : sortCol
  const dirRef = table === 'na' ? naSortDir : sortDir
  if (colRef.value !== col) return 'unfold_more'
  return dirRef.value === 'asc' ? 'expand_less' : 'expand_more'
}

const sortedNeedsAction = computed(() => sortCases(needsActionCases.value, naSortCol.value, naSortDir.value))
const sortedAllCases = computed(() => sortCases(store.cases, sortCol.value, sortDir.value))

function applyFilters() {
  const dateParams = filterDateRange.value ? dateRangeToParams(filterDateRange.value) : {}
  store.setFilters({
    search: searchQuery.value || undefined,
    risk_level: filterRisk.value?.toLowerCase(),
    verdict: filterAction.value?.toLowerCase(),
    status: filterStatus.value?.toLowerCase(),
    ...dateParams,
  })
}

function clearFilters() {
  searchQuery.value = ''
  filterRisk.value = undefined
  filterAction.value = undefined
  filterStatus.value = undefined
  filterDateRange.value = undefined
  store.setFilters({})
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 300)
}

function openCase(id: string) {
  router.push({ name: 'case-detail', params: { id } })
}

async function quickAllow(caseId: string) {
  allowingCaseId.value = caseId
  try {
    await resolveCase(caseId, 'allowed')
    await store.fetchCases()
    if (paginatedNeedsCases.value.length === 0 && naPage.value > 1) {
      naPage.value--
    }
  } finally {
    allowingCaseId.value = null
  }
}

async function quickBlock(caseId: string) {
  blockingCaseId.value = caseId
  try {
    await resolveCase(caseId, 'blocked')
    await store.fetchCases()
    if (paginatedNeedsCases.value.length === 0 && naPage.value > 1) {
      naPage.value--
    }
  } finally {
    blockingCaseId.value = null
  }
}

onMounted(() => {
  store.fetchCases()
})
</script>

<template>
  <div class="cases-page">
    <GlobalFiltersBar />

    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Cases</h1>
        <span class="count-badge">{{ store.total.toLocaleString() }}</span>
      </div>
      <div class="header-right">
        <button class="btn-outline">
          <span class="material-symbols-rounded btn-icon">download</span>
          Export CSV
        </button>
        <button class="btn-outline" @click="store.fetchCases()">
          <span class="material-symbols-rounded btn-icon">refresh</span>
          Refresh
        </button>
      </div>
    </div>

    <!-- Overview KPIs -->
    <div class="cases-kpis">
      <div class="kpi-card">
        <div class="kpi-icon-wrap kpi-icon-total">
          <span class="material-symbols-rounded">folder_open</span>
        </div>
        <div class="kpi-info">
          <span class="kpi-value">{{ store.total }}</span>
          <span class="kpi-label">Total Cases</span>
        </div>
      </div>
      <div class="kpi-card kpi-card-accent">
        <div class="kpi-icon-wrap kpi-icon-action">
          <span class="material-symbols-rounded">pending_actions</span>
        </div>
        <div class="kpi-info">
          <span class="kpi-value">{{ needsActionCases.length }}</span>
          <span class="kpi-label">Needs Review</span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon-wrap kpi-icon-resolved">
          <span class="material-symbols-rounded">check_circle</span>
        </div>
        <div class="kpi-info">
          <span class="kpi-value">{{ resolvedCount }}</span>
          <span class="kpi-label">Resolved</span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon-wrap kpi-icon-risk">
          <span class="material-symbols-rounded">warning</span>
        </div>
        <div class="kpi-info">
          <span class="kpi-value">{{ highRiskCount }}</span>
          <span class="kpi-label">High / Critical Risk</span>
        </div>
      </div>
    </div>

    <!-- Needs Action -->
    <div v-if="needsActionCases.length" class="needs-action">
      <div class="na-header">
        <div class="na-header-left">
          <span class="material-symbols-rounded na-icon">notification_important</span>
          <h2>Needs Action</h2>
          <span class="na-count">{{ needsActionCases.length }}</span>
        </div>
        <span class="na-hint">These cases have been analyzed and are awaiting your review</span>
      </div>
      <table class="na-table">
        <thead>
          <tr>
            <th class="na-th-id sortable-th" @click="toggleSort('na', 'case_number')">CASE <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'case_number') }}</span></th>
            <th class="na-th-subject">SUBJECT</th>
            <th class="na-th-sender">SENDER</th>
            <th class="na-th-score sortable-th" @click="toggleSort('na', 'score')">SCORE <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'score') }}</span></th>
            <th class="na-th-risk sortable-th" @click="toggleSort('na', 'risk')">RISK <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'risk') }}</span></th>
            <th class="na-th-status sortable-th" @click="toggleSort('na', 'status')">STATUS <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'status') }}</span></th>
            <th class="na-th-actions">ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in paginatedNeedsCases"
            :key="c.id"
            class="na-row"
            @click="openCase(c.id)"
          >
            <td class="na-td-id">#{{ c.case_number }}</td>
            <td class="na-td-subject">{{ c.email_subject ?? '(No Subject)' }}</td>
            <td class="na-td-sender">{{ c.email_sender ?? '—' }}</td>
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
            </td>
            <td>
              <span
                class="pill-badge"
                :style="{ color: statusColor(c.status), background: statusBg(c.status) }"
              >{{ capitalize(c.status) }}</span>
            </td>
            <td class="na-td-actions">
              <button
                class="na-icon-btn na-icon-allow"
                :disabled="allowingCaseId === c.id"
                @click.stop="quickAllow(c.id)"
                title="Allow this case"
              >
                <span class="material-symbols-rounded">{{ allowingCaseId === c.id ? 'progress_activity' : 'check' }}</span>
              </button>
              <button
                class="na-icon-btn na-icon-block"
                :disabled="blockingCaseId === c.id"
                @click.stop="quickBlock(c.id)"
                title="Block this case"
              >
                <span class="material-symbols-rounded">{{ blockingCaseId === c.id ? 'progress_activity' : 'close' }}</span>
              </button>
              <span class="material-symbols-rounded na-arrow">arrow_forward</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="na-pagination">
        <div class="pagination-left">
          <span class="na-page-info">{{ naStartItem }}-{{ naEndItem }} of {{ needsActionCases.length }}</span>
          <select class="size-select" :value="naPageSize" @change="naPageSize = Number(($event.target as HTMLSelectElement).value); naPage = 1">
            <option v-for="s in [5, 10, 15, 20]" :key="s" :value="s">{{ s }} / page</option>
          </select>
        </div>
        <div v-if="naTotalPages > 1" class="na-page-btns">
          <button class="page-btn" :disabled="naPage <= 1" @click="naPage--">Prev</button>
          <template v-for="p in naTotalPages" :key="p">
            <button class="page-btn" :class="{ active: p === naPage }" @click="naPage = p">{{ p }}</button>
          </template>
          <button class="page-btn" :disabled="naPage >= naTotalPages" @click="naPage++">Next</button>
        </div>
      </div>
    </div>


    <!-- All Cases -->
    <div class="all-cases-header">
      <h2>All Cases</h2>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="search-input-wrapper">
        <span class="material-symbols-rounded search-icon">search</span>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="Search subjects, senders, IDs..."
          @input="onSearchInput"
        />
      </div>
      <select v-model="filterRisk" class="filter-select" @change="applyFilters">
        <option :value="undefined">Risk Level</option>
        <option v-for="opt in RISK_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
      </select>
      <select v-model="filterAction" class="filter-select" @change="applyFilters">
        <option :value="undefined">Action</option>
        <option v-for="opt in ACTION_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
      </select>
      <select v-model="filterStatus" class="filter-select" @change="applyFilters">
        <option :value="undefined">Status</option>
        <option v-for="opt in STATUS_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
      </select>
      <select v-model="filterDateRange" class="filter-select" @change="applyFilters">
        <option :value="undefined">Date Range</option>
        <option v-for="opt in DATE_RANGE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <a v-if="hasActiveFilters" href="#" class="clear-link" @click.prevent="clearFilters">Clear Filters</a>
      <span class="results-count">Showing {{ startItem }}-{{ endItem }} of {{ store.total.toLocaleString() }}</span>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div v-if="store.loading" class="loading-state">Loading cases...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th style="width: 65px" class="sortable-th" @click="toggleSort('all', 'case_number')">CASE ID <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'case_number') }}</span></th>
            <th style="width: 130px" class="sortable-th" @click="toggleSort('all', 'received')">RECEIVED <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'received') }}</span></th>
            <th>SUBJECT</th>
            <th style="width: 160px">SENDER</th>
            <th style="width: 55px" class="sortable-th" @click="toggleSort('all', 'score')">SCORE <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'score') }}</span></th>
            <th style="width: 70px" class="sortable-th" @click="toggleSort('all', 'risk')">RISK <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'risk') }}</span></th>
            <th style="width: 85px" class="sortable-th" @click="toggleSort('all', 'action')">ACTION <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'action') }}</span></th>
            <th style="width: 70px" class="sortable-th" @click="toggleSort('all', 'status')">STATUS <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'status') }}</span></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in sortedAllCases"
            :key="c.id"
            class="case-row"
            @click="openCase(c.id)"
          >
            <td>
              <span class="case-id">#{{ c.case_number }}</span>
            </td>
            <td class="cell-date">{{ formatDate(c.email_received_at ?? c.created_at) }}</td>
            <td class="cell-subject">{{ c.email_subject ?? '(No Subject)' }}</td>
            <td class="cell-sender">{{ c.email_sender ?? '—' }}</td>
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
              <span
                v-if="c.verdict"
                class="pill-badge"
                :style="{ color: actionColor(c.verdict), background: actionBg(c.verdict) }"
              >{{ capitalize(c.verdict) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span
                class="pill-badge"
                :style="{ color: statusColor(c.status), background: statusBg(c.status) }"
              >{{ capitalize(c.status) }}</span>
            </td>
          </tr>
          <tr v-if="store.cases.length === 0">
            <td colspan="8" class="empty-state">No cases found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <div class="pagination-left">
        <span class="pagination-info">
          Showing {{ startItem }}-{{ endItem }} of {{ store.total.toLocaleString() }} cases
        </span>
        <select class="size-select" :value="store.size" @change="store.setSize(Number(($event.target as HTMLSelectElement).value))">
          <option v-for="s in [5, 10, 15, 20]" :key="s" :value="s">{{ s }} / page</option>
        </select>
      </div>
      <div v-if="totalPages > 1" class="pagination-buttons">
        <button
          class="page-btn"
          :disabled="store.page <= 1"
          @click="store.setPage(store.page - 1)"
        >Previous</button>
        <template v-for="p in pageNumbers" :key="p">
          <span v-if="p === '...'" class="page-ellipsis">...</span>
          <button
            v-else
            class="page-btn"
            :class="{ active: p === store.page }"
            @click="store.setPage(p as number)"
          >{{ p }}</button>
        </template>
        <button
          class="page-btn"
          :disabled="store.page >= totalPages"
          @click="store.setPage(store.page + 1)"
        >Next</button>
        </div>
    </div>
  </div>
</template>

<style scoped>
.cases-page {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.case-row {
  cursor: pointer;
}

/* ── KPI Cards ── */
.cases-kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
}

.kpi-card-accent {
  border-color: var(--accent-cyan);
  background: rgba(0, 212, 255, 0.04);
}

.kpi-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-icon-wrap .material-symbols-rounded {
  font-size: 20px;
}

.kpi-icon-total {
  background: rgba(107, 114, 128, 0.12);
  color: #9CA3AF;
}

.kpi-icon-action {
  background: rgba(0, 212, 255, 0.12);
  color: var(--accent-cyan);
}

.kpi-icon-resolved {
  background: rgba(34, 197, 94, 0.12);
  color: #22C55E;
}

.kpi-icon-risk {
  background: rgba(239, 68, 68, 0.12);
  color: #EF4444;
}

.kpi-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.kpi-value {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
}

.kpi-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* ── Needs Action ── */
.needs-action {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--accent-cyan);
  overflow: hidden;
}

.na-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
}

.na-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.na-icon {
  font-size: 20px;
  color: var(--accent-cyan);
}

.na-header h2 {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.na-count {
  background: var(--accent-cyan);
  color: var(--bg-primary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  padding: 1px 8px;
  border-radius: 10px;
}

.na-hint {
  font-size: 11px;
  color: var(--text-muted);
}

/* ── Needs Action Table ── */
.na-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
}

.na-table thead th {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.na-th-id { width: 70px; }
.na-th-subject { }
.na-th-sender { width: 200px; }
.na-th-score { width: 65px; }
.na-th-risk { width: 80px; }
.na-th-status { width: 90px; }
.na-th-actions { width: 80px; text-align: right; }

.na-row {
  cursor: pointer;
  transition: background 0.1s;
  border-bottom: 1px solid var(--border-color);
}

.na-row:last-child {
  border-bottom: none;
}

.na-row:hover {
  background: rgba(0, 212, 255, 0.04);
}

.na-row td {
  padding: 10px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  vertical-align: middle;
}

.na-td-id {
  font-weight: 700;
  color: var(--accent-cyan) !important;
  font-size: 13px !important;
}

.na-td-subject {
  color: var(--text-primary) !important;
  font-size: 13px !important;
  max-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.na-td-sender {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.na-td-actions {
  text-align: right;
  white-space: nowrap;
}

.na-icon-btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
  vertical-align: middle;
}

.na-icon-btn .material-symbols-rounded {
  font-size: 16px;
}

.na-icon-allow {
  color: #22C55E;
}

.na-icon-allow:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.15);
}

.na-icon-allow:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.na-icon-block {
  color: #EF4444;
}

.na-icon-block:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.15);
}

.na-icon-block:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.na-arrow {
  font-size: 16px;
  color: var(--text-muted);
  margin-left: 6px;
  vertical-align: middle;
}

/* ── NA Pagination ── */
.na-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  border-top: 1px solid var(--border-color);
}

.na-page-info {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.na-page-btns {
  display: flex;
  gap: 4px;
}

/* ── All Cases Header ── */
.all-cases-header {
  margin-top: 4px;
}

.all-cases-header h2 {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

@media (max-width: 1000px) {
  .cases-kpis {
    grid-template-columns: repeat(2, 1fr);
  }
  .na-th-sender,
  .na-td-sender {
    display: none;
  }
}
</style>
