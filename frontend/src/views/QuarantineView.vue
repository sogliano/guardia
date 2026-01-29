<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useQuarantineStore } from '@/stores/quarantine'
import { formatDateLong, formatTimeAgo, shortId, capitalize } from '@/utils/formatters'
import { riskColor, riskBg } from '@/utils/colors'
import GlobalFiltersBar from '@/components/GlobalFiltersBar.vue'

const store = useQuarantineStore()

const pendingCount = computed(() => store.total)
const detail = computed(() => store.emailDetail)

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

function selectItem(id: string) {
  store.selectItem(id)
}

// Auto-select first item when list loads
watch(() => store.items, (items) => {
  if (items.length > 0 && !store.selectedId) {
    store.selectItem(items[0].id)
  }
})

onMounted(() => {
  store.fetchQuarantined()
})
</script>

<template>
  <div class="quarantine-page">
    <GlobalFiltersBar />
    <!-- Header -->
    <div class="page-header quarantine-header">
      <div class="header-left">
        <h1>Quarantine Queue</h1>
        <span class="pending-badge">
          <span class="material-symbols-rounded badge-icon">warning</span>
          {{ pendingCount }} pending
        </span>
      </div>
      <div class="header-right">
        <button class="btn-success" :disabled="store.actionLoading">
          <span class="material-symbols-rounded btn-icon">send</span>
          Release Selected
        </button>
        <button class="btn-outline" :disabled="store.actionLoading">
          <span class="material-symbols-rounded btn-icon">more_horiz</span>
          Batch Actions
        </button>
      </div>
    </div>

    <!-- Split Panel -->
    <div class="split-panel">
      <!-- Left: Queue List -->
      <div class="queue-panel">
        <div class="queue-header">
          <span class="queue-title">Quarantined Emails</span>
          <span class="queue-count">{{ store.total }} items</span>
        </div>

        <div v-if="store.loading" class="queue-loading">Loading...</div>

        <div v-else class="queue-list">
          <div
            v-for="item in store.items"
            :key="item.id"
            class="queue-item"
            :class="{ selected: store.selectedId === item.id }"
            @click="selectItem(item.id)"
          >
            <div class="item-main">
              <div class="item-top">
                <span class="item-sender">{{ item.email_sender ?? 'Unknown sender' }}</span>
                <span
                  class="pill-badge"
                  :style="{ color: riskColor(item.risk_level), background: riskBg(item.risk_level) }"
                >{{ item.final_score !== null ? item.final_score.toFixed(2) : '—' }}</span>
              </div>
              <div class="item-subject">{{ item.email_subject ?? '(No Subject)' }}</div>
              <div class="item-time">{{ formatTimeAgo(item.email_received_at ?? item.created_at) }}</div>
            </div>
          </div>
          <div v-if="store.items.length === 0" class="queue-empty">
            No quarantined emails
          </div>
        </div>
      </div>

      <!-- Right: Email Preview -->
      <div class="preview-panel">
        <div v-if="store.detailLoading" class="preview-loading">Loading email detail...</div>
        <div v-else-if="!detail" class="preview-empty">
          <span class="material-symbols-rounded empty-icon">mail</span>
          <p>Select an email to preview</p>
        </div>
        <div v-else class="preview-content">
          <!-- Preview Header -->
          <div class="preview-header">
            <h2 class="preview-subject">{{ detail.subject ?? '(No Subject)' }}</h2>
            <a href="#" class="view-full-link">View Full</a>
          </div>

          <!-- Metadata -->
          <div class="preview-meta">
            <div class="meta-row">
              <span class="meta-label">From</span>
              <span class="meta-value">{{ detail.sender_name ? `${detail.sender_name} <${detail.sender_email}>` : detail.sender_email }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">To</span>
              <span class="meta-value">{{ detail.recipient_email }}</span>
            </div>
            <div v-if="detail.reply_to" class="meta-row">
              <span class="meta-label">Reply-To</span>
              <span class="meta-value">{{ detail.reply_to }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Date</span>
              <span class="meta-value">{{ formatDateLong(detail.received_at) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Message-ID</span>
              <span class="meta-value meta-mono">{{ detail.message_id }}</span>
            </div>
          </div>

          <!-- Auth Results -->
          <div class="auth-row">
            <span :class="['auth-badge', authBadgeClass('spf')]">SPF: {{ authStatus('spf') }}</span>
            <span :class="['auth-badge', authBadgeClass('dkim')]">DKIM: {{ authStatus('dkim') }}</span>
            <span :class="['auth-badge', authBadgeClass('dmarc')]">DMARC: {{ authStatus('dmarc') }}</span>
          </div>

          <!-- Body Preview -->
          <div v-if="detail.body_preview" class="body-preview">
            <pre class="body-text">{{ detail.body_preview }}</pre>
          </div>

          <!-- AI Analysis -->
          <div v-if="detail.ai_explanation" class="ai-analysis">
            <div class="ai-header">
              <span class="material-symbols-rounded ai-icon">psychology</span>
              <span class="ai-title">AI Analysis</span>
            </div>
            <p class="ai-text">{{ detail.ai_explanation }}</p>
          </div>

          <!-- Action Buttons -->
          <div class="preview-actions">
            <button
              class="action-btn release"
              :disabled="store.actionLoading"
              @click="store.release(store.selectedId!)"
            >
              <span class="material-symbols-rounded btn-icon">send</span>
              {{ store.actionLoading ? 'Processing...' : 'Release' }}
            </button>
            <button
              class="action-btn keep"
              :disabled="store.actionLoading"
              @click="store.keep(store.selectedId!)"
            >
              <span class="material-symbols-rounded btn-icon">lock</span>
              {{ store.actionLoading ? 'Processing...' : 'Keep Quarantined' }}
            </button>
            <button
              class="action-btn delete"
              :disabled="store.actionLoading"
              @click="store.remove(store.selectedId!)"
            >
              <span class="material-symbols-rounded btn-icon">delete</span>
              {{ store.actionLoading ? 'Processing...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quarantine-page {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - var(--topbar-height));
}

.quarantine-header {
  flex-shrink: 0;
}

/* ── Pending Badge ── */
.pending-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 10px;
  border-radius: 12px;
  background: rgba(245, 158, 11, 0.15);
  color: #F59E0B;
  font-size: 12px;
  font-weight: 600;
}

.badge-icon {
  font-size: 14px;
}

/* ── Split Panel ── */
.split-panel {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

/* ── Queue Panel (Left) ── */
.queue-panel {
  width: 480px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.queue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
}

.queue-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.queue-count {
  font-size: 12px;
  color: var(--text-muted);
}

.queue-loading {
  padding: 32px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.queue-list {
  flex: 1;
  overflow-y: auto;
}

.queue-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.12s;
  border-left: 3px solid transparent;
}

.queue-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.queue-item.selected {
  background: rgba(0, 212, 255, 0.06);
  border-left-color: #00D4FF;
}

.queue-item:last-child {
  border-bottom: none;
}

.item-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.item-sender {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.item-top .pill-badge {
  flex-shrink: 0;
  margin-left: 8px;
}

.item-subject {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-time {
  font-size: 11px;
  color: var(--text-muted);
}

.queue-empty {
  padding: 48px 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

/* ── Preview Panel (Right) ── */
.preview-panel {
  flex: 1;
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  overflow-y: auto;
}

.preview-loading {
  padding: 48px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
}

.preview-empty p {
  font-size: 14px;
  margin: 0;
}

.preview-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.preview-subject {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.view-full-link {
  font-size: 13px;
  color: #00D4FF;
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
}

.view-full-link:hover {
  text-decoration: underline;
}

/* Metadata */
.preview-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--border-radius-sm);
}

.meta-row {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.meta-label {
  width: 80px;
  flex-shrink: 0;
  color: var(--text-muted);
  font-weight: 500;
}

.meta-value {
  color: var(--text-secondary);
  word-break: break-all;
}

.meta-mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 11px;
}

/* Auth Results */
.auth-row {
  display: flex;
  gap: 8px;
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 12px;
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

/* Body Preview */
.body-preview {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--border-radius-sm);
  overflow: auto;
  max-height: 200px;
}

.body-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

/* AI Analysis */
.ai-analysis {
  padding: 16px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: var(--border-radius-sm);
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.ai-icon {
  font-size: 18px;
  color: #F59E0B;
}

.ai-title {
  font-size: 13px;
  font-weight: 700;
  color: #F59E0B;
}

.ai-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

/* Action Buttons */
.preview-actions {
  display: flex;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
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

/* ── Responsive ── */
@media (max-width: 1200px) {
  .split-panel {
    flex-direction: column;
  }
  .queue-panel {
    width: 100%;
    max-height: 300px;
  }
}
</style>
