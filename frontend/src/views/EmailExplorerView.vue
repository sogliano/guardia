<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useEmailsStore } from '@/stores/emails'
import { formatDate, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg, actionColor, actionBg } from '@/utils/colors'
import { computePageNumbers } from '@/utils/pagination'
import { RISK_OPTIONS, DATE_RANGE_OPTIONS, dateRangeToParams } from '@/constants/filterOptions'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'
import MultiSelect from '@/components/common/MultiSelect.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { ingestEmail } from '@/services/emailService'

const store = useEmailsStore()

const searchQuery = ref('')
const filterShow = ref<string | undefined>()
const filterRisk = ref<string[]>(RISK_OPTIONS.slice())
const filterDate = ref<string | undefined>()
const showIngestModal = ref(false)
const ingesting = ref(false)
const ingestError = ref('')

const showOptions = ['With Case', 'No Case']

let searchTimer: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.ceil(store.total / store.size))
const startItem = computed(() => (store.page - 1) * store.size + 1)
const endItem = computed(() => Math.min(store.page * store.size, store.total))

const pageNumbers = computed(() => computePageNumbers(store.page, totalPages.value))

const validationErrors = ref<Record<string, string>>({})

const ingestForm = ref({
  message_id: '',
  sender_email: '',
  sender_name: '',
  recipient_email: '',
  subject: '',
  body_text: '',
})

function applyFilters() {
  const dateParams = filterDate.value ? dateRangeToParams(filterDate.value) : {}
  store.setFilters({
    search: searchQuery.value || undefined,
    risk_level: filterRisk.value.length === 1
      ? filterRisk.value[0]?.toLowerCase()
      : undefined,
    ...dateParams,
  })
}

watch(filterRisk, () => {
  applyFilters()
})

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 300)
}

function openIngestModal() {
  showIngestModal.value = true
  ingestError.value = ''
  validationErrors.value = {}
  ingestForm.value = {
    message_id: `test-${Date.now()}@guardia.local`,
    sender_email: '',
    sender_name: '',
    recipient_email: 'security@strikesecurity.io',
    subject: '',
    body_text: '',
  }
}

function closeIngestModal() {
  showIngestModal.value = false
}

function validateIngestForm(): boolean {
  validationErrors.value = {}

  if (!ingestForm.value.sender_email) {
    validationErrors.value.sender_email = 'Sender email is required'
  } else if (!ingestForm.value.sender_email.includes('@')) {
    validationErrors.value.sender_email = 'Invalid email format'
  }

  if (!ingestForm.value.recipient_email) {
    validationErrors.value.recipient_email = 'Recipient email is required'
  } else if (!ingestForm.value.recipient_email.includes('@')) {
    validationErrors.value.recipient_email = 'Invalid email format'
  }

  if (!ingestForm.value.message_id) {
    validationErrors.value.message_id = 'Message ID is required'
  }

  return Object.keys(validationErrors.value).length === 0
}

async function submitIngest() {
  if (!validateIngestForm()) return

  ingesting.value = true
  ingestError.value = ''
  try {
    await ingestEmail({
      message_id: ingestForm.value.message_id,
      sender_email: ingestForm.value.sender_email,
      sender_name: ingestForm.value.sender_name || null,
      reply_to: null,
      recipient_email: ingestForm.value.recipient_email,
      recipients_cc: [],
      subject: ingestForm.value.subject || null,
      body_text: ingestForm.value.body_text || null,
      body_html: null,
      headers: {},
      urls: [],
      attachments: [],
      auth_results: {},
      received_at: null,
    })
    closeIngestModal()
    await store.fetchEmails()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } } }
    ingestError.value = error.response?.data?.detail || 'Failed to ingest email'
  } finally{
    ingesting.value = false
  }
}

onMounted(() => {
  store.fetchEmails()
})
</script>

<template>
  <div class="emails-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Emails</h1>
        <span class="count-badge">{{ store.total.toLocaleString() }} emails</span>
        <p class="subtitle">Browse and analyze ingested email messages</p>
      </div>
      <div class="header-right">
        <GlobalFiltersBar />
      </div>
    </div>

    <!-- Ingest Email Modal -->
    <div v-if="showIngestModal" class="modal-overlay" @click="closeIngestModal">
      <div class="modal-card" @click.stop>
        <div class="modal-header">
          <h2>Ingest Email</h2>
          <button class="close-btn" @click="closeIngestModal">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <form @submit.prevent="submitIngest" class="modal-body">
          <div class="form-group">
            <label>Message ID</label>
            <input
              v-model="ingestForm.message_id"
              type="text"
              required
              class="form-input"
              :class="{ 'input-error': validationErrors.message_id }"
            />
            <span v-if="validationErrors.message_id" class="error-text">
              {{ validationErrors.message_id }}
            </span>
          </div>
          <div class="form-group">
            <label>Sender Email *</label>
            <input
              v-model="ingestForm.sender_email"
              type="email"
              required
              class="form-input"
              placeholder="attacker@example.com"
              :class="{ 'input-error': validationErrors.sender_email }"
            />
            <span v-if="validationErrors.sender_email" class="error-text">
              {{ validationErrors.sender_email }}
            </span>
          </div>
          <div class="form-group">
            <label>Sender Name</label>
            <input v-model="ingestForm.sender_name" type="text" class="form-input" placeholder="John Doe" />
          </div>
          <div class="form-group">
            <label>Recipient Email *</label>
            <input
              v-model="ingestForm.recipient_email"
              type="email"
              required
              class="form-input"
              :class="{ 'input-error': validationErrors.recipient_email }"
            />
            <span v-if="validationErrors.recipient_email" class="error-text">
              {{ validationErrors.recipient_email }}
            </span>
          </div>
          <div class="form-group">
            <label>Subject</label>
            <input v-model="ingestForm.subject" type="text" class="form-input" placeholder="Urgent: Password Reset Required" />
          </div>
          <div class="form-group">
            <label>Body Text</label>
            <textarea v-model="ingestForm.body_text" class="form-textarea" rows="6" placeholder="Email body content..."></textarea>
          </div>
          <div v-if="ingestError" class="error-message">{{ ingestError }}</div>
          <div class="modal-footer">
            <button type="button" class="btn-outline" @click="closeIngestModal" :disabled="ingesting">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="ingesting">
              <span v-if="ingesting" class="material-symbols-rounded btn-icon spinning">progress_activity</span>
              <span v-else class="material-symbols-rounded btn-icon">upload</span>
              {{ ingesting ? 'Ingesting...' : 'Ingest Email' }}
            </button>
          </div>
        </form>
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
      <MultiSelect
        v-model="filterRisk"
        :options="RISK_OPTIONS.map(v => ({ value: v, label: v }))"
        placeholder="Risk Level"
      />
      <select v-model="filterDate" class="filter-select" @change="applyFilters">
        <option :value="undefined">Date Range</option>
        <option v-for="opt in DATE_RANGE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="table-card">
      <LoadingState v-if="store.loading" message="Loading emails..." />
      <div v-else-if="store.error" class="error-state">
        <span class="material-symbols-rounded">error</span>
        <p>{{ store.error }}</p>
        <button @click="store.fetchEmails()" class="retry-btn">Retry</button>
      </div>
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
                {{ email.final_score !== null && email.final_score !== undefined ? (email.final_score * 100).toFixed(0) + '%' : '—' }}
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
            @click="typeof p === 'number' && store.setPage(p)"
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

.email-row {
  cursor: pointer;
}

.cell-checkbox {
  text-align: center;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.close-btn .material-symbols-rounded {
  font-size: 20px;
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  background: var(--bg-inset);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #00D4FF;
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.error-message {
  padding: 10px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--border-radius);
  color: #EF4444;
  font-size: 12px;
  font-family: var(--font-mono);
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.input-error {
  border-color: #EF4444;
}

.error-text {
  color: #EF4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

.error-state {
  text-align: center;
  padding: 64px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.error-state span {
  font-size: 48px;
  color: #EF4444;
}

.error-state p {
  font-family: var(--font-mono);
  font-size: 14px;
  color: #EF4444;
  margin: 0;
}

.retry-btn {
  background: #EF4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #DC2626;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
