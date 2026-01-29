<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { formatDate, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg, statusColor, statusBg } from '@/utils/colors'
import { computePageNumbers } from '@/utils/pagination'
import { RISK_OPTIONS, ACTION_OPTIONS, STATUS_OPTIONS, DATE_OPTIONS } from '@/constants/filterOptions'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'

const router = useRouter()
const store = useCasesStore()

const searchQuery = ref('')
const filterRisk = ref<string | undefined>()
const filterAction = ref<string | undefined>()
const filterStatus = ref<string | undefined>()
const filterDateRange = ref<string | undefined>()

let searchTimer: ReturnType<typeof setTimeout> | null = null

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

function applyFilters() {
  store.setFilters({
    search: searchQuery.value || undefined,
    risk_level: filterRisk.value?.toLowerCase(),
    verdict: filterAction.value?.toLowerCase(),
    status: filterStatus.value?.toLowerCase(),
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
      <div class="na-list">
        <div
          v-for="c in needsActionCases"
          :key="c.id"
          class="na-item"
          @click="openCase(c.id)"
        >
          <div class="na-item-left">
            <span class="na-case-id">#{{ c.case_number }}</span>
            <span class="na-subject">{{ c.email_subject ?? '(No Subject)' }}</span>
          </div>
          <div class="na-item-center">
            <span class="na-sender">{{ c.email_sender ?? '—' }}</span>
          </div>
          <div class="na-item-right">
            <span class="score-val" :style="{ color: scoreColor(c.final_score) }">
              {{ c.final_score !== null ? c.final_score.toFixed(2) : '—' }}
            </span>
            <span
              v-if="c.risk_level"
              class="pill-badge"
              :style="{ color: riskColor(c.risk_level), background: riskBg(c.risk_level) }"
            >{{ capitalize(c.risk_level) }}</span>
            <span
              class="pill-badge"
              :style="{ color: statusColor(c.status), background: statusBg(c.status) }"
            >{{ capitalize(c.status) }}</span>
            <span class="material-symbols-rounded na-arrow">arrow_forward</span>
          </div>
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
        <option v-for="opt in DATE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
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
            <th style="width: 65px">CASE ID</th>
            <th style="width: 130px">RECEIVED</th>
            <th>SUBJECT</th>
            <th style="width: 160px">SENDER</th>
            <th style="width: 55px">SCORE</th>
            <th style="width: 70px">RISK</th>
            <th style="width: 85px">ACTION</th>
            <th style="width: 70px">STATUS</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in store.cases"
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
                {{ c.final_score !== null ? c.final_score.toFixed(2) : '—' }}
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
    <div v-if="totalPages > 1" class="pagination">
      <span class="pagination-info">
        Showing {{ startItem }}-{{ endItem }} of {{ store.total.toLocaleString() }} cases
      </span>
      <div class="pagination-buttons">
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

.na-list {
  display: flex;
  flex-direction: column;
}

.na-item {
  display: flex;
  align-items: center;
  padding: 12px 18px;
  cursor: pointer;
  transition: background 0.1s;
  border-bottom: 1px solid var(--border-color);
}

.na-item:last-child {
  border-bottom: none;
}

.na-item:hover {
  background: rgba(0, 212, 255, 0.04);
}

.na-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.na-case-id {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--accent-cyan);
  flex-shrink: 0;
}

.na-subject {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.na-item-center {
  flex: 0 0 220px;
  min-width: 0;
}

.na-sender {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.na-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.na-arrow {
  font-size: 16px;
  color: var(--text-muted);
  margin-left: 4px;
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
  .na-item-center {
    display: none;
  }
}
</style>
