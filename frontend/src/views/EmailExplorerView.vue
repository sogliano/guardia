<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useEmailsStore } from '@/stores/emails'
import { formatDate, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg } from '@/utils/colors'
import { computePageNumbers } from '@/utils/pagination'
import { RISK_OPTIONS, DATE_OPTIONS } from '@/constants/filterOptions'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'

const store = useEmailsStore()

const searchQuery = ref('')
const filterShow = ref<string | undefined>()
const filterRisk = ref<string | undefined>()
const filterDate = ref<string | undefined>()

const showOptions = ['With Case', 'No Case']

let searchTimer: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.ceil(store.total / store.size))
const startItem = computed(() => (store.page - 1) * store.size + 1)
const endItem = computed(() => Math.min(store.page * store.size, store.total))

const pageNumbers = computed(() => computePageNumbers(store.page, totalPages.value))

function applyFilters() {
  store.setFilters({
    search: searchQuery.value || undefined,
    risk_level: filterRisk.value?.toLowerCase(),
  })
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 300)
}

onMounted(() => {
  store.fetchEmails()
})
</script>

<template>
  <div class="emails-page">
    <GlobalFiltersBar />

    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Email Explorer</h1>
        <span class="count-badge">{{ store.total.toLocaleString() }} emails</span>
      </div>
      <div class="header-right">
        <button class="btn-primary">
          <span class="material-symbols-rounded btn-icon">upload</span>
          Ingest Email
        </button>
        <button class="btn-outline">
          <span class="material-symbols-rounded btn-icon">download</span>
          Export
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
          placeholder="Search by subject, sender..."
          @input="onSearchInput"
        />
      </div>
      <select v-model="filterShow" class="filter-select" @change="applyFilters">
        <option :value="undefined">Show All</option>
        <option v-for="opt in showOptions" :key="opt" :value="opt">{{ opt }}</option>
      </select>
      <select v-model="filterRisk" class="filter-select" @change="applyFilters">
        <option :value="undefined">Risk Level</option>
        <option v-for="opt in RISK_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
      </select>
      <select v-model="filterDate" class="filter-select" @change="applyFilters">
        <option :value="undefined">Date Range</option>
        <option v-for="opt in DATE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div v-if="store.loading" class="loading-state">Loading emails...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th style="width: 40px"><input type="checkbox" disabled /></th>
            <th>SENDER</th>
            <th>SUBJECT</th>
            <th style="width: 80px">RISK</th>
            <th style="width: 90px">ACTION</th>
            <th style="width: 130px">DATE</th>
            <th style="width: 60px">SCORE</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="email in store.emails" :key="email.id" class="email-row">
            <td class="cell-checkbox"><input type="checkbox" /></td>
            <td class="cell-sender">{{ email.sender_email }}</td>
            <td class="cell-subject">{{ email.subject ?? '(No Subject)' }}</td>
            <td>
              <span
                v-if="email.risk_level"
                class="pill-badge"
                :style="{ color: riskColor(email.risk_level), background: riskBg(email.risk_level) }"
              >{{ capitalize(email.risk_level) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span
                v-if="email.verdict"
                class="pill-badge"
                :style="{ color: actionColor(email.verdict), background: actionBg(email.verdict) }"
              >{{ capitalize(email.verdict) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="cell-date">{{ formatDate(email.received_at) }}</td>
            <td>
              <span class="score-val" :style="{ color: scoreColor(email.final_score) }">
                {{ email.final_score !== null && email.final_score !== undefined ? email.final_score.toFixed(2) : '—' }}
              </span>
            </td>
          </tr>
          <tr v-if="store.emails.length === 0">
            <td colspan="7" class="empty-state">No emails found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <span class="pagination-info">
        Showing {{ startItem }}-{{ endItem }} of {{ store.total.toLocaleString() }} emails
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
.emails-page {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.email-row {
  cursor: pointer;
}

.cell-checkbox {
  text-align: center;
}
</style>
