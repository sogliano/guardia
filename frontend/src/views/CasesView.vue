<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { resolveCase } from '@/services/caseService'
import type { Case } from '@/types/case'
import { formatDate, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg, statusColor, statusBg } from '@/utils/colors'
import { computePageNumbers } from '@/utils/pagination'
import { RISK_OPTIONS, ACTION_OPTIONS, STATUS_OPTIONS, DATE_RANGE_OPTIONS, dateRangeToParams } from '@/constants/filterOptions'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'
import QuarantineQueue from '@/components/cases/QuarantineQueue.vue'
import MultiSelect from '@/components/common/MultiSelect.vue'
import DateRangePicker from '@/components/common/DateRangePicker.vue'

const router = useRouter()
const route = useRoute()
const store = useCasesStore()

type TabId = 'all' | 'needs-action' | 'quarantine'
const activeTab = ref<TabId>((route.query.tab as TabId) || 'all')

function setTab(tab: TabId) {
  activeTab.value = tab
  router.replace({ query: tab === 'all' ? {} : { tab } })
}

const searchQuery = ref('')
const filterRisk = ref<string[]>(RISK_OPTIONS.slice())
const filterAction = ref<string[]>(ACTION_OPTIONS.slice())
const filterStatus = ref<string[]>(STATUS_OPTIONS.slice())
const filterDateRange = ref<{ from: string | null; to: string | null }>({ from: null, to: null })

const naSearchQuery = ref('')
const naFilterRisk = ref<string[]>(RISK_OPTIONS.slice())
const naFilterAction = ref<string[]>(ACTION_OPTIONS.slice())
const naFilterDateRange = ref<{ from: string | null; to: string | null }>({ from: null, to: null })
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
  return searchQuery.value ||
    filterRisk.value.length !== RISK_OPTIONS.length ||
    filterAction.value.length !== ACTION_OPTIONS.length ||
    filterStatus.value.length !== STATUS_OPTIONS.length ||
    filterDateRange.value.from ||
    filterDateRange.value.to
})

const pageNumbers = computed(() => computePageNumbers(store.page, totalPages.value))

// Overview computeds
const naHasActiveFilters = computed(() => {
  return naSearchQuery.value ||
    naFilterRisk.value.length !== RISK_OPTIONS.length ||
    naFilterAction.value.length !== ACTION_OPTIONS.length ||
    naFilterDateRange.value.from ||
    naFilterDateRange.value.to
})

function clearNaFilters() {
  naSearchQuery.value = ''
  naFilterRisk.value = RISK_OPTIONS.slice()
  naFilterAction.value = ACTION_OPTIONS.slice()
  naFilterDateRange.value = { from: null, to: null }
}

const needsActionCases = computed(() => {
  let base = store.cases.filter(c => c.status === 'analyzed' || c.status === 'quarantined')
  const q = naSearchQuery.value.trim().toLowerCase()
  if (q) {
    base = base.filter(c =>
      (c.email_subject ?? '').toLowerCase().includes(q) ||
      (c.email_sender ?? '').toLowerCase().includes(q) ||
      String(c.case_number ?? '').includes(q)
    )
  }
  if (naFilterRisk.value.length > 0 && naFilterRisk.value.length < RISK_OPTIONS.length) {
    base = base.filter(c => c.risk_level && naFilterRisk.value.map(r => r.toLowerCase()).includes(c.risk_level.toLowerCase()))
  }
  if (naFilterAction.value.length > 0 && naFilterAction.value.length < ACTION_OPTIONS.length) {
    base = base.filter(c => c.verdict && naFilterAction.value.map(a => a.toLowerCase()).includes(c.verdict.toLowerCase()))
  }
  if (naFilterDateRange.value.from || naFilterDateRange.value.to) {
    base = base.filter(c => {
      const receivedDate = c.email_received_at ?? c.created_at
      if (!receivedDate) return false
      if (naFilterDateRange.value.from && receivedDate < naFilterDateRange.value.from) return false
      if (naFilterDateRange.value.to && receivedDate > naFilterDateRange.value.to + 'T23:59:59') return false
      return true
    })
  }
  return base
})

const resolvedCount = computed(() => store.cases.filter(c => c.status === 'resolved').length)
const blockedCount = computed(() => store.blockedCases.length)
const riskOrder: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 }
const statusOrder: Record<string, number> = { quarantined: 4, analyzed: 3, analyzing: 2, pending: 1, resolved: 0 }

function getSortValue(c: Case, col: string): string | number {
  if (col === 'case_number') return c.case_number ?? 0
  if (col === 'received') return c.email_received_at ?? c.created_at ?? ''
  if (col === 'score') return c.final_score ?? -1
  if (col === 'heuristic') return c.heuristic_score ?? -1
  if (col === 'ml') return c.ml_score ?? -1
  if (col === 'llm') return c.llm_score ?? -1
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
  store.setFilters({
    search: searchQuery.value || undefined,
    risk_level: filterRisk.value.length > 0 && filterRisk.value.length < RISK_OPTIONS.length
      ? filterRisk.value[0]?.toLowerCase()
      : undefined,
    verdict: filterAction.value.length > 0 && filterAction.value.length < ACTION_OPTIONS.length
      ? filterAction.value[0]?.toLowerCase()
      : undefined,
    status: filterStatus.value.length > 0 && filterStatus.value.length < STATUS_OPTIONS.length
      ? filterStatus.value[0]?.toLowerCase()
      : undefined,
    date_from: filterDateRange.value.from || undefined,
    date_to: filterDateRange.value.to || undefined,
  })
}

function clearFilters() {
  searchQuery.value = ''
  filterRisk.value = RISK_OPTIONS.slice()
  filterAction.value = ACTION_OPTIONS.slice()
  filterStatus.value = STATUS_OPTIONS.slice()
  filterDateRange.value = { from: null, to: null }
  store.setFilters({})
}

// Watch for filter changes and apply automatically
watch([filterRisk, filterAction, filterStatus, filterDateRange], () => {
  applyFilters()
}, { deep: true })

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 300)
}

function formatCategory(cat: string): string {
  return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
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
  } catch (err) {
    console.error('Error allowing case:', err)
    alert(`Failed to allow case: ${err instanceof Error ? err.message : 'Unknown error'}`)
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
  } catch (err) {
    console.error('Error blocking case:', err)
    alert(`Failed to block case: ${err instanceof Error ? err.message : 'Unknown error'}`)
  } finally {
    blockingCaseId.value = null
  }
}

function exportCSV() {
  const rows = store.cases
  if (!rows.length) return
  const headers = ['Case #', 'Subject', 'Sender', 'Score', 'Risk', 'Verdict', 'Status', 'Received', 'Created']
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`
  const lines = [
    headers.join(','),
    ...rows.map(c => [
      c.case_number,
      escape(c.email_subject ?? ''),
      escape(c.email_sender ?? ''),
      c.final_score !== null ? `${(c.final_score * 100).toFixed(0)}%` : '',
      c.risk_level ?? '',
      c.verdict ?? '',
      c.status,
      c.email_received_at ?? '',
      c.created_at,
    ].join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `guardia-cases-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  store.fetchCases()
})
</script>

<template>
  <div class="cases-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Cases</h1>
        <span class="count-badge">{{ store.total.toLocaleString() }}</span>
        <p class="subtitle">Manage and review analyzed email cases</p>
      </div>
      <div class="header-right">
        <button class="btn-outline" @click="exportCSV">
          <span class="material-symbols-rounded btn-icon">download</span>
          Export CSV
        </button>
        <button class="btn-outline" @click="store.fetchCases()">
          <span class="material-symbols-rounded btn-icon">refresh</span>
          Refresh
        </button>
        <GlobalFiltersBar />
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
          <span class="material-symbols-rounded">block</span>
        </div>
        <div class="kpi-info">
          <span class="kpi-value">{{ blockedCount }}</span>
          <span class="kpi-label">Blocked</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'all' }"
        @click="setTab('all')"
      >
        <span class="material-symbols-rounded tab-icon">folder_open</span>
        All Cases
        <span class="tab-count">{{ store.total }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'needs-action' }"
        @click="setTab('needs-action')"
      >
        <span class="material-symbols-rounded tab-icon">pending_actions</span>
        Needs Action
        <span v-if="needsActionCases.length" class="tab-count tab-count-accent">{{ needsActionCases.length }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'quarantine' }"
        @click="setTab('quarantine')"
      >
        <span class="material-symbols-rounded tab-icon">shield</span>
        Quarantine &amp; Blocked
        <span v-if="store.quarantineAndBlockedCases.length" class="tab-count tab-count-warning">{{ store.quarantineAndBlockedCases.length }}</span>
      </button>
    </div>

    <!-- Tab: Quarantine Queue -->
    <QuarantineQueue v-if="activeTab === 'quarantine'" />

    <!-- Tab: Needs Action -->
    <template v-if="activeTab === 'needs-action'">
      <div v-if="!needsActionCases.length" class="empty-tab">
        <span class="material-symbols-rounded empty-tab-icon">check_circle</span>
        <p>All caught up — no cases need action right now</p>
      </div>
      <template v-else>
        <div class="filter-bar">
          <div class="search-input-wrapper">
            <span class="material-symbols-rounded search-icon">search</span>
            <input
              v-model="naSearchQuery"
              type="text"
              class="search-input"
              placeholder="Search subjects, senders, IDs..."
            />
          </div>
          <MultiSelect
            v-model="naFilterRisk"
            :options="RISK_OPTIONS.map(v => ({ value: v, label: v }))"
            placeholder="Risk Level"
          />
          <MultiSelect
            v-model="naFilterAction"
            :options="ACTION_OPTIONS.map(v => ({ value: v, label: v }))"
            placeholder="Action"
          />
          <DateRangePicker v-model="naFilterDateRange" />
          <a v-if="naHasActiveFilters" href="#" class="clear-link" @click.prevent="clearNaFilters">Clear Filters</a>
          <span class="results-count">{{ needsActionCases.length }} cases</span>
        </div>
        <div class="table-card">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 50px" class="sortable-th" @click="toggleSort('na', 'case_number')">ID <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'case_number') }}</span></th>
                <th>SUBJECT</th>
                <th style="width: 180px">SENDER</th>
                <th style="width: 70px" class="sortable-th" @click="toggleSort('na', 'score')">SCORE <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'score') }}</span></th>
                <th style="width: 75px" class="sortable-th" @click="toggleSort('na', 'risk')">RISK <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'risk') }}</span></th>
                <th style="width: 90px" class="sortable-th" @click="toggleSort('na', 'action')">ACTION <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'action') }}</span></th>
                <th style="width: 120px">CATEGORY</th>
                <th style="width: 80px" class="sortable-th" @click="toggleSort('na', 'status')">STATUS <span class="material-symbols-rounded sort-icon">{{ sortIcon('na', 'status') }}</span></th>
                <th style="width: 90px">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in paginatedNeedsCases"
                :key="c.id"
                class="case-row"
                @click="openCase(c.id)"
              >
                <td><span class="case-id">#{{ c.case_number }}</span></td>
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
                  <span v-if="c.threat_category" class="cell-category">{{ formatCategory(c.threat_category) }}</span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td>
                  <span
                    class="pill-badge"
                    :style="{ color: statusColor(c.status), background: statusBg(c.status) }"
                  >{{ capitalize(c.status) }}</span>
                </td>
                <td class="td-actions">
                  <button
                    class="action-icon-btn action-allow"
                    :disabled="allowingCaseId === c.id"
                    @click.stop="quickAllow(c.id)"
                    title="Allow this case"
                  >
                    <span class="material-symbols-rounded">{{ allowingCaseId === c.id ? 'progress_activity' : 'check' }}</span>
                  </button>
                  <button
                    class="action-icon-btn action-block"
                    :disabled="blockingCaseId === c.id"
                    @click.stop="quickBlock(c.id)"
                    title="Block this case"
                  >
                    <span class="material-symbols-rounded">{{ blockingCaseId === c.id ? 'progress_activity' : 'close' }}</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination">
          <div class="pagination-left">
            <span class="pagination-info">Showing {{ naStartItem }}-{{ naEndItem }} of {{ needsActionCases.length }}</span>
            <select class="size-select" :value="naPageSize" @change="naPageSize = Number(($event.target as HTMLSelectElement).value); naPage = 1">
              <option v-for="s in [5, 10, 15, 20]" :key="s" :value="s">{{ s }} / page</option>
            </select>
          </div>
          <div v-if="naTotalPages > 1" class="pagination-buttons">
            <button class="page-btn" :disabled="naPage <= 1" @click="naPage--">Previous</button>
            <template v-for="p in naTotalPages" :key="p">
              <button class="page-btn" :class="{ active: p === naPage }" @click="naPage = p">{{ p }}</button>
            </template>
            <button class="page-btn" :disabled="naPage >= naTotalPages" @click="naPage++">Next</button>
          </div>
        </div>
      </template>
    </template>

    <!-- Tab: All Cases -->
    <template v-if="activeTab === 'all'">

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
      <MultiSelect
        v-model="filterRisk"
        :options="RISK_OPTIONS.map(v => ({ value: v, label: v }))"
        placeholder="Risk Level"
      />
      <MultiSelect
        v-model="filterAction"
        :options="ACTION_OPTIONS.map(v => ({ value: v, label: v }))"
        placeholder="Action"
      />
      <MultiSelect
        v-model="filterStatus"
        :options="STATUS_OPTIONS.map(v => ({ value: v, label: v }))"
        placeholder="Status"
      />
      <DateRangePicker v-model="filterDateRange" />
      <a v-if="hasActiveFilters" href="#" class="clear-link" @click.prevent="clearFilters">Clear Filters</a>
      <span class="results-count">Showing {{ startItem }}-{{ endItem }} of {{ store.total.toLocaleString() }}</span>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div v-if="store.loading" class="loading-state">Loading cases...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th style="width: 50px" class="sortable-th" @click="toggleSort('all', 'case_number')">ID <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'case_number') }}</span></th>
            <th style="width: 120px" class="sortable-th" @click="toggleSort('all', 'received')">RECEIVED <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'received') }}</span></th>
            <th>SUBJECT</th>
            <th style="width: 180px">SENDER</th>
            <th style="width: 70px" class="sortable-th" @click="toggleSort('all', 'score')">SCORE <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'score') }}</span></th>
            <th style="width: 75px" class="sortable-th" @click="toggleSort('all', 'risk')">RISK <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'risk') }}</span></th>
            <th style="width: 90px" class="sortable-th" @click="toggleSort('all', 'action')">ACTION <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'action') }}</span></th>
            <th style="width: 80px" class="sortable-th" @click="toggleSort('all', 'status')">STATUS <span class="material-symbols-rounded sort-icon">{{ sortIcon('all', 'status') }}</span></th>
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

    </template><!-- /tab: all -->
  </div>
</template>

<style scoped>
.cases-page {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
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

/* ── Action Buttons (Needs Action tab) ── */
.td-actions {
  text-align: right;
  white-space: nowrap;
}

.action-icon-btn {
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

.action-icon-btn .material-symbols-rounded {
  font-size: 16px;
}

.action-allow {
  color: #22C55E;
}

.action-allow:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.15);
}

.action-block {
  color: #EF4444;
}

.action-block:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.15);
}

.action-icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Tabs ── */
.tabs-bar {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.15s;
}

.tab-btn:hover {
  color: var(--text-secondary);
}

.tab-btn.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
}

.tab-icon {
  font-size: 16px;
}

.tab-count {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(107, 114, 128, 0.15);
  color: var(--text-muted);
}

.tab-count-accent {
  background: rgba(0, 212, 255, 0.15);
  color: var(--accent-cyan);
}

.tab-count-warning {
  background: rgba(245, 158, 11, 0.15);
  color: #F59E0B;
}

/* ── Empty Tab ── */
.empty-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  color: var(--text-muted);
}

.empty-tab-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
  color: #22C55E;
}

.empty-tab p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

@media (max-width: 1000px) {
  .cases-kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}

</style>
