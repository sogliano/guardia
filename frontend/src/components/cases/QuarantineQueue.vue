<script setup lang="ts">
import { computed, watch } from 'vue'
import { useCasesStore } from '@/stores/cases'
import { formatTimeAgo, formatDateLong, capitalize } from '@/utils/formatters'
import { scoreColor, riskColor, riskBg } from '@/utils/colors'

const store = useCasesStore()

const quarantined = computed(() => store.quarantinedCases)
const detail = computed(() => store.quarantineEmailDetail)
const selectedId = computed(() => store.quarantineSelectedId)

function authStatus(key: string): string {
  if (!detail.value?.auth_results) return 'N/A'
  const val = detail.value.auth_results[key]
  if (typeof val === 'string') return val
  if (typeof val === 'object' && val !== null && 'result' in (val as Record<string, unknown>)) {
    return String((val as Record<string, unknown>).result)
  }
  return val ? 'pass' : 'N/A'
}

function authBadgeClass(key: string): string {
  const status = authStatus(key).toLowerCase()
  if (status === 'pass') return 'auth-pass'
  if (status === 'fail' || status === 'softfail') return 'auth-fail'
  return 'auth-none'
}

function toggleRow(id: string) {
  if (selectedId.value === id) {
    store.clearQuarantineSelection()
  } else {
    store.selectQuarantineItem(id)
  }
}

watch(quarantined, (items) => {
  if (items.length > 0 && !selectedId.value) {
    store.selectQuarantineItem(items[0].id)
  }
})
</script>

<template>
  <div class="quarantine-queue">
    <!-- Empty state -->
    <div v-if="quarantined.length === 0" class="q-empty">
      <span class="material-symbols-rounded empty-icon">verified_user</span>
      <p>No quarantined emails</p>
      <span class="empty-hint">All clear — no emails are waiting for review</span>
    </div>

    <!-- Table -->
    <div v-else class="q-table-card">
      <table class="q-table">
        <thead>
          <tr>
            <th class="q-th" style="width: 220px">SENDER</th>
            <th class="q-th">SUBJECT</th>
            <th class="q-th" style="width: 60px">SCORE</th>
            <th class="q-th" style="width: 90px">RISK</th>
            <th class="q-th" style="width: 110px">CATEGORY</th>
            <th class="q-th" style="width: 80px">RECEIVED</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="c in quarantined" :key="c.id">
            <!-- Row -->
            <tr
              class="q-row"
              :class="{ 'q-row-selected': selectedId === c.id }"
              @click="toggleRow(c.id)"
            >
              <td class="q-td-sender">{{ c.email_sender ?? 'Unknown' }}</td>
              <td class="q-td-subject">{{ c.email_subject ?? '(No Subject)' }}</td>
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
                <span v-if="c.threat_category" class="pill-badge pill-category">
                  {{ capitalize(c.threat_category.replace('_', ' ')) }}
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="q-td-time">{{ formatTimeAgo(c.email_received_at ?? c.created_at) }}</td>
            </tr>

            <!-- Expanded Detail -->
            <tr v-if="selectedId === c.id" class="q-detail-row">
              <td colspan="6" class="q-detail-cell">
                <div v-if="store.quarantineDetailLoading" class="q-detail-loading">
                  Loading email detail...
                </div>
                <div v-else-if="detail" class="q-detail">
                  <!-- Top: Metadata + AI Analysis -->
                  <div class="q-detail-top">
                    <div class="q-meta-col">
                      <h4>Email Metadata</h4>
                      <div class="meta-row">
                        <span class="meta-label">From:</span>
                        <span class="meta-value">{{ detail.sender_name ? `${detail.sender_name} <${detail.sender_email}>` : detail.sender_email }}</span>
                      </div>
                      <div class="meta-row">
                        <span class="meta-label">To:</span>
                        <span class="meta-value">{{ detail.recipient_email }}</span>
                      </div>
                      <div v-if="detail.reply_to" class="meta-row">
                        <span class="meta-label">Reply-To:</span>
                        <span class="meta-value meta-danger">{{ detail.reply_to }}</span>
                      </div>
                      <div class="meta-row">
                        <span class="meta-label">Date:</span>
                        <span class="meta-value">{{ formatDateLong(detail.received_at) }}</span>
                      </div>
                      <div class="meta-row">
                        <span class="meta-label">Msg-ID:</span>
                        <span class="meta-value meta-mono">{{ detail.message_id }}</span>
                      </div>
                    </div>
                    <div class="q-ai-col">
                      <h4>AI Analysis</h4>
                      <p v-if="detail.ai_explanation" class="ai-text">{{ detail.ai_explanation }}</p>
                      <p v-else class="ai-text text-muted">No AI explanation available</p>
                      <div class="ai-info-row">
                        <span class="ai-info-label">Confidence:</span>
                        <span class="ai-info-value" :style="{ color: scoreColor(detail.final_score) }">
                          {{ detail.final_score !== null ? (detail.final_score * 100).toFixed(0) + '%' : '—' }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Auth Badges -->
                  <div class="q-auth-row">
                    <span class="auth-label">Authentication:</span>
                    <span :class="['auth-badge', authBadgeClass('spf')]">SPF: {{ authStatus('spf') }}</span>
                    <span :class="['auth-badge', authBadgeClass('dkim')]">DKIM: {{ authStatus('dkim') }}</span>
                    <span :class="['auth-badge', authBadgeClass('dmarc')]">DMARC: {{ authStatus('dmarc') }}</span>
                  </div>

                  <!-- Body Preview -->
                  <div v-if="detail.body_preview" class="q-body-section">
                    <h4>Body Preview</h4>
                    <div class="q-body-box">
                      <pre class="q-body-text">{{ detail.body_preview }}</pre>
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="q-actions">
                    <button
                      class="action-btn release"
                      :disabled="store.quarantineActionLoading"
                      @click.stop="store.releaseCase(c.id)"
                    >
                      <span class="material-symbols-rounded btn-icon">send</span>
                      {{ store.quarantineActionLoading ? 'Processing...' : 'Release Email' }}
                    </button>
                    <button
                      class="action-btn keep"
                      :disabled="store.quarantineActionLoading"
                      @click.stop="store.keepQuarantinedCase(c.id)"
                    >
                      <span class="material-symbols-rounded btn-icon">lock</span>
                      {{ store.quarantineActionLoading ? 'Processing...' : 'Keep Quarantined' }}
                    </button>
                    <button
                      class="action-btn delete"
                      :disabled="store.quarantineActionLoading"
                      @click.stop="store.deleteQuarantinedCase(c.id)"
                    >
                      <span class="material-symbols-rounded btn-icon">delete</span>
                      {{ store.quarantineActionLoading ? 'Processing...' : 'Delete' }}
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          </template>
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

/* Empty */
.q-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
}

.q-empty p {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.empty-hint {
  font-size: 12px;
  margin-top: 4px;
}

/* Table */
.q-table-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.q-table {
  width: 100%;
  border-collapse: collapse;
}

.q-th {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  text-align: left;
  padding: 10px 16px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.q-row {
  cursor: pointer;
  transition: background 0.1s;
  border-bottom: 1px solid var(--border-color);
}

.q-row:hover {
  background: rgba(0, 212, 255, 0.04);
}

.q-row-selected {
  background: rgba(0, 212, 255, 0.06);
}

.q-row td {
  padding: 10px 16px;
  font-size: 12px;
  color: var(--text-secondary);
  vertical-align: middle;
}

.q-td-sender {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-primary) !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.q-td-subject {
  color: var(--text-secondary) !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 0;
}

.q-td-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted) !important;
}

.score-val {
  font-family: var(--font-mono);
  font-weight: 600;
  font-size: 12px;
}

.pill-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.pill-category {
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent-cyan);
}

/* Expanded Detail */
.q-detail-row {
  background: rgba(0, 212, 255, 0.03);
}

.q-detail-cell {
  padding: 0 !important;
}

.q-detail {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-top: 1px solid var(--border-color);
}

.q-detail-loading {
  padding: 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.q-detail-top {
  display: flex;
  gap: 32px;
}

.q-meta-col, .q-ai-col {
  flex: 1;
  min-width: 0;
}

.q-detail h4 {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.meta-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.meta-label {
  width: 70px;
  flex-shrink: 0;
  color: var(--text-muted);
  font-weight: 600;
  font-family: var(--font-mono);
  font-size: 11px;
}

.meta-value {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  word-break: break-all;
}

.meta-danger {
  color: #EF4444;
}

.meta-mono {
  font-size: 10px;
  color: var(--text-muted);
}

.ai-text {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.ai-info-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.ai-info-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.ai-info-value {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
}

/* Auth */
.q-auth-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.auth-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 10px;
  border-radius: 11px;
  font-size: 11px;
  font-weight: 600;
}

.auth-pass {
  background: rgba(34, 197, 94, 0.15);
  color: #22C55E;
}

.auth-fail {
  background: rgba(239, 68, 68, 0.15);
  color: #EF4444;
}

.auth-none {
  background: rgba(107, 114, 128, 0.15);
  color: #6B7280;
}

/* Body */
.q-body-box {
  padding: 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  max-height: 200px;
  overflow: auto;
}

.q-body-text {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

/* Actions */
.q-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: var(--border-radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.action-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn .btn-icon {
  font-size: 16px;
}

.action-btn.release {
  background: #22C55E;
  color: #fff;
}

.action-btn.keep {
  background: #F97316;
  color: #fff;
}

.action-btn.delete {
  background: #EF4444;
  color: #fff;
}

.text-muted {
  color: var(--text-muted);
}

@media (max-width: 1000px) {
  .q-detail-top {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
