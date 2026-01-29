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
</style>
