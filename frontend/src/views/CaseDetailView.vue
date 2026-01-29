<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { CaseDetail, Analysis, Evidence, CaseNote } from '@/types/case'
import { fetchCaseDetail, addCaseNote, updateCaseNote, resolveCase, createFPReview } from '@/services/caseService'
import { scoreColor } from '@/utils/colors'

const route = useRoute()
const router = useRouter()
const caseId = route.params.id as string

const caseData = ref<CaseDetail | null>(null)
const loading = ref(true)
const error = ref('')
const activeTab = ref<'overview' | 'email' | 'pipeline'>('overview')

// Note form
const newNote = ref('')
const addingNote = ref(false)

// Action modal
const showActionModal = ref(false)
const actionStep = ref(1)
const actionVerdict = ref('')
const actionIsFP = ref(false)
const actionFPNotes = ref('')
const actionSubmitting = ref(false)

// Email content section toggles
const showHeaders = ref(false)
const showBody = ref(true)
const showUrls = ref(true)
const showAttachments = ref(true)

// Pipeline stage expand/collapse
const expandedStages = ref<Set<string>>(new Set())

function toggleStage(id: string) {
  if (expandedStages.value.has(id)) {
    expandedStages.value.delete(id)
  } else {
    expandedStages.value.add(id)
  }
}

// Note editing
const editingNoteId = ref<string | null>(null)
const editingNoteContent = ref('')

const heuristicAnalysis = computed(() => caseData.value?.analyses.find(a => a.stage === 'heuristic'))
const mlAnalysis = computed(() => caseData.value?.analyses.find(a => a.stage === 'ml'))
const llmAnalysis = computed(() => caseData.value?.analyses.find(a => a.stage === 'llm'))

const authResults = computed(() => {
  const auth = caseData.value?.email?.auth_results ?? {}
  return {
    spf: String(auth.spf ?? 'none').toLowerCase(),
    dkim: String(auth.dkim ?? 'none').toLowerCase(),
    dmarc: String(auth.dmarc ?? 'none').toLowerCase(),
  }
})

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function formatMs(ms: number | null): string {
  if (ms === null) return '—'
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}

function formatScore(score: number | null): string {
  return score != null ? (score * 100).toFixed(0) + '%' : '—'
}

function riskBadgeClass(level: string | null): string {
  if (!level) return 'badge-muted'
  const map: Record<string, string> = {
    low: 'badge-success', medium: 'badge-warn', high: 'badge-high', critical: 'badge-critical'
  }
  return map[level] ?? 'badge-muted'
}

function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    pending: 'badge-muted', analyzing: 'badge-warn', analyzed: 'badge-info',
    quarantined: 'badge-critical', resolved: 'badge-success',
  }
  return map[status] ?? 'badge-muted'
}

function verdictBadgeClass(verdict: string | null): string {
  if (!verdict) return 'badge-muted'
  const map: Record<string, string> = {
    allowed: 'badge-success', warned: 'badge-warn', quarantined: 'badge-high', blocked: 'badge-critical'
  }
  return map[verdict] ?? 'badge-muted'
}

function authBadgeClass(result: string): string {
  return result === 'pass' ? 'auth-pass' : 'auth-fail'
}

function severityBadgeClass(severity: string): string {
  const map: Record<string, string> = {
    critical: 'badge-critical', high: 'badge-high', medium: 'badge-warn', low: 'badge-success'
  }
  return map[severity] ?? 'badge-muted'
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const threatCategoryMeta: Record<string, { label: string; color: string; bg: string; desc: string }> = {
  bec_impersonation: {
    label: 'BEC',
    color: '#8B5CF6',
    bg: 'rgba(139, 92, 246, 0.15)',
    desc: 'Business Email Compromise: suplantación de identidad ejecutiva para solicitar transferencias o datos sensibles',
  },
  credential_phishing: {
    label: 'Credential Phishing',
    color: '#EF4444',
    bg: 'rgba(239, 68, 68, 0.15)',
    desc: 'Intento de robar credenciales mediante páginas falsas de login',
  },
  malware_payload: {
    label: 'Malware',
    color: '#DC2626',
    bg: 'rgba(220, 38, 38, 0.15)',
    desc: 'Email con archivos adjuntos o enlaces que distribuyen código malicioso',
  },
  generic_phishing: {
    label: 'Phishing',
    color: '#F97316',
    bg: 'rgba(249, 115, 22, 0.15)',
    desc: 'Intento genérico de phishing sin categoría específica',
  },
  clean: {
    label: 'Clean',
    color: '#D1D5DB',
    bg: 'rgba(209, 213, 219, 0.12)',
    desc: 'Email analizado sin amenazas detectadas',
  },
}

const stageNames: Record<string, string> = {
  heuristic: 'Heuristic Engine',
  ml: 'ML Classifier',
  llm: 'LLM Explainer',
}

const stageIcons: Record<string, string> = {
  heuristic: 'rule',
  ml: 'psychology',
  llm: 'smart_toy',
}

const stageDescs: Record<string, string> = {
  heuristic: 'Deterministic rules: SPF, DKIM, DMARC, domain reputation, URL analysis, urgency patterns',
  ml: 'DistilBERT fine-tuned classifier (66M params) — probabilistic risk scoring',
  llm: 'AI-generated natural language explanation of the analysis',
}

const evidenceTypeLabels: Record<string, string> = {
  auth_spf_fail: 'SPF Authentication',
  auth_spf_neutral: 'SPF Neutral',
  auth_dkim_fail: 'DKIM Signature',
  auth_dmarc_fail: 'DMARC Policy',
  auth_dmarc_missing: 'DMARC Missing',
  auth_reply_to_mismatch: 'Reply-To Mismatch',
  auth_compound_failure: 'Compound Auth Failure',
  domain_blacklisted: 'Blocklisted Domain',
  domain_typosquatting: 'Typosquatting',
  domain_suspicious_tld: 'Suspicious TLD',
  url_shortener: 'URL Shortener',
  url_ip_based: 'IP-Based URL',
  url_suspicious: 'Suspicious URL',
  keyword_urgency: 'Urgency Language',
  keyword_phishing: 'Phishing Keywords',
  keyword_caps_abuse: 'Caps Abuse',
  attachment_suspicious_ext: 'Suspicious Attachment',
  attachment_double_ext: 'Double Extension Attack',
  ml_high_score: 'ML Threat Signal',
  ceo_impersonation: 'CEO Impersonation',
  sender_impersonation: 'Brand Impersonation',
}

function evidenceLabel(type: string): string {
  return evidenceTypeLabels[type] ?? type.replace(/_/g, ' ')
}

const severityOrder: Record<string, number> = {
  critical: 0, high: 1, medium: 2, low: 3,
}

function sortedEvidences(evidences: Evidence[]): Evidence[] {
  return [...evidences].sort((a, b) => (severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4))
}

function isStageUnavailable(analysis: Analysis): boolean {
  if (analysis.stage === 'ml') {
    return analysis.score === 0 && analysis.confidence === 0 && analysis.execution_time_ms === 0
  }
  if (analysis.stage === 'llm') {
    return !analysis.explanation || analysis.explanation.toLowerCase().includes('unavailable')
  }
  return false
}

function stageStatusLabel(analysis: Analysis): string {
  if (isStageUnavailable(analysis)) return 'Unavailable'
  if (analysis.stage === 'llm') {
    return analysis.explanation ? 'Explained' : 'No explanation'
  }
  if (analysis.score === null) return 'No data'
  if (analysis.score < 0.3) return 'Clean'
  if (analysis.score < 0.6) return 'Suspicious'
  return 'Threat detected'
}

function stageStatusColor(analysis: Analysis): string {
  if (isStageUnavailable(analysis)) return 'var(--text-muted)'
  if (analysis.stage === 'llm') return analysis.explanation ? 'var(--color-info)' : 'var(--text-muted)'
  if (analysis.score === null) return 'var(--text-muted)'
  return scoreColor(analysis.score)
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    caseData.value = await fetchCaseDetail(caseId)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load case'
  } finally {
    loading.value = false
  }
}

function openActionModal() {
  actionStep.value = 1
  actionVerdict.value = ''
  actionIsFP.value = false
  actionFPNotes.value = ''
  showActionModal.value = true
}

function closeActionModal() {
  showActionModal.value = false
}

async function submitAction() {
  if (!actionVerdict.value || !caseData.value) return
  actionSubmitting.value = true
  try {
    await resolveCase(caseId, actionVerdict.value)
    if (actionIsFP.value) {
      await createFPReview(caseId, {
        decision: 'confirmed_fp',
        notes: actionFPNotes.value || undefined,
      })
    }
    showActionModal.value = false
    await loadData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to resolve'
  } finally {
    actionSubmitting.value = false
  }
}

async function handleAddNote() {
  if (!newNote.value.trim()) return
  addingNote.value = true
  try {
    await addCaseNote(caseId, { content: newNote.value.trim() })
    newNote.value = ''
    await loadData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to add note'
  } finally {
    addingNote.value = false
  }
}

function startEditNote(note: CaseNote) {
  editingNoteId.value = note.id
  editingNoteContent.value = note.content
}

function cancelEditNote() {
  editingNoteId.value = null
  editingNoteContent.value = ''
}

async function handleUpdateNote(note: CaseNote) {
  if (!editingNoteContent.value.trim() || !caseData.value) return
  try {
    await updateCaseNote(caseData.value.id, note.id, editingNoteContent.value.trim())
    editingNoteId.value = null
    editingNoteContent.value = ''
    await loadData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to update note'
  }
}

onMounted(loadData)
</script>

<template>
  <div class="case-detail">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <span class="material-symbols-rounded spin">progress_activity</span>
      Loading case...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn-primary" @click="loadData">Retry</button>
    </div>

    <!-- Content -->
    <template v-else-if="caseData">
      <!-- Header -->
      <div class="detail-header">
        <button class="btn-back" @click="router.push('/cases')">
          <span class="material-symbols-rounded">arrow_back</span>
        </button>
        <div class="header-info">
          <h1>Case #{{ caseData.case_number }}</h1>
          <div class="header-badges">
            <span class="badge" :class="statusBadgeClass(caseData.status)">{{ capitalize(caseData.status) }}</span>
            <span v-if="caseData.risk_level" class="badge" :class="riskBadgeClass(caseData.risk_level)">{{ capitalize(caseData.risk_level) }}</span>
            <span v-if="caseData.verdict" class="badge" :class="verdictBadgeClass(caseData.verdict)">{{ capitalize(caseData.verdict) }}</span>
          </div>
        </div>
        <div class="header-score" v-if="caseData.final_score !== null">
          <div class="score-ring">
            <svg viewBox="0 0 80 80" class="score-svg">
              <circle cx="40" cy="40" r="34" fill="none" stroke="var(--border-color)" stroke-width="5" />
              <circle
                class="score-arc"
                cx="40" cy="40" r="34" fill="none"
                :stroke="scoreColor(caseData.final_score)"
                stroke-width="5"
                stroke-linecap="round"
                :stroke-dasharray="`${(caseData.final_score ?? 0) * 213.6} 213.6`"
                stroke-dashoffset="213.6"
                transform="rotate(-90 40 40)"
              />
            </svg>
            <div class="score-ring-text">
              <span class="score-ring-value" :style="{ color: scoreColor(caseData.final_score) }">
                {{ (caseData.final_score * 100).toFixed(0) }}
              </span>
              <span class="score-ring-label">SCORE</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Bar -->
      <div class="tab-bar">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'overview' }"
          @click="activeTab = 'overview'"
        >
          <span class="material-symbols-rounded">dashboard</span>
          Overview
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'email' }"
          @click="activeTab = 'email'"
        >
          <span class="material-symbols-rounded">email</span>
          Email Content
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'pipeline' }"
          @click="activeTab = 'pipeline'"
        >
          <span class="material-symbols-rounded">analytics</span>
          Pipeline Results
        </button>
      </div>

      <!-- ============================================================ -->
      <!-- TAB 1: Overview -->
      <!-- ============================================================ -->
      <div v-if="activeTab === 'overview'" class="tab-content">
        <!-- Email Information -->
        <div class="card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">mail</span>
            Email Information
          </h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">From</span>
              <span class="info-value">
                {{ caseData.email?.sender_name ? `${caseData.email.sender_name} <${caseData.email.sender_email}>` : caseData.email?.sender_email ?? '—' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">To</span>
              <span class="info-value">{{ caseData.email?.recipient_email ?? '—' }}</span>
            </div>
            <div class="info-item" v-if="caseData.email?.recipients_cc?.length">
              <span class="info-label">CC</span>
              <span class="info-value">{{ caseData.email.recipients_cc.join(', ') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Subject</span>
              <span class="info-value">{{ caseData.email?.subject ?? '(No Subject)' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Received</span>
              <span class="info-value">{{ formatDate(caseData.email?.received_at ?? null) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Threat Category</span>
              <span class="info-value">
                <span
                  v-if="caseData.threat_category && threatCategoryMeta[caseData.threat_category]"
                  class="category-badge tooltip-wrap tooltip-bottom"
                  :style="{
                    color: threatCategoryMeta[caseData.threat_category].color,
                    background: threatCategoryMeta[caseData.threat_category].bg,
                  }"
                  :data-tooltip="threatCategoryMeta[caseData.threat_category].desc"
                >{{ threatCategoryMeta[caseData.threat_category].label }}</span>
                <span v-else-if="caseData.threat_category">{{ capitalize(caseData.threat_category.replace(/_/g, ' ')) }}</span>
                <span v-else>—</span>
              </span>
            </div>
          </div>
        </div>

        <!-- AI Analysis Summary -->
        <div v-if="llmAnalysis?.explanation" class="card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">smart_toy</span>
            AI Analysis Summary
          </h3>
          <p class="llm-explanation">{{ llmAnalysis.explanation }}</p>
          <div class="llm-meta">
            <span v-if="llmAnalysis.execution_time_ms">{{ formatMs(llmAnalysis.execution_time_ms) }}</span>
          </div>
        </div>

        <!-- Authentication Status -->
        <div class="card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">shield</span>
            Authentication Status
          </h3>
          <div class="auth-badges">
            <div
              class="auth-badge tooltip-wrap"
              :class="authBadgeClass(authResults.spf)"
              data-tooltip="SPF (Sender Policy Framework): Verifica que el servidor que envió el email está autorizado por el dominio del remitente. PASS = autorizado, FAIL/SOFTFAIL = no autorizado."
            >
              <span class="material-symbols-rounded auth-icon">
                {{ authResults.spf === 'pass' ? 'check_circle' : 'cancel' }}
              </span>
              <span class="auth-name">SPF</span>
              <span class="auth-result">{{ authResults.spf }}</span>
              <span class="material-symbols-rounded auth-help">help</span>
            </div>
            <div
              class="auth-badge tooltip-wrap"
              :class="authBadgeClass(authResults.dkim)"
              data-tooltip="DKIM (DomainKeys Identified Mail): Verifica la integridad del email mediante firma digital. PASS = no fue alterado en tránsito, FAIL = posible manipulación."
            >
              <span class="material-symbols-rounded auth-icon">
                {{ authResults.dkim === 'pass' ? 'check_circle' : 'cancel' }}
              </span>
              <span class="auth-name">DKIM</span>
              <span class="auth-result">{{ authResults.dkim }}</span>
              <span class="material-symbols-rounded auth-help">help</span>
            </div>
            <div
              class="auth-badge tooltip-wrap"
              :class="authBadgeClass(authResults.dmarc)"
              data-tooltip="DMARC (Domain-based Message Authentication): Política del dominio que combina SPF y DKIM. PASS = cumple la política, FAIL = no cumple, posible suplantación de identidad."
            >
              <span class="material-symbols-rounded auth-icon">
                {{ authResults.dmarc === 'pass' ? 'check_circle' : 'cancel' }}
              </span>
              <span class="auth-name">DMARC</span>
              <span class="auth-result">{{ authResults.dmarc }}</span>
              <span class="material-symbols-rounded auth-help">help</span>
            </div>
          </div>
        </div>

        <!-- Risk Score Summary -->
        <div class="card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">speed</span>
            Risk Score Breakdown
          </h3>
          <div class="score-summary">
            <div class="score-main">
              <span class="score-big" :style="{ color: scoreColor(caseData.final_score) }">
                {{ formatScore(caseData.final_score) }}
              </span>
              <span class="score-desc">Final Score</span>
            </div>
            <!-- Score bar -->
            <div class="score-bar-container">
              <div class="score-bar-track">
                <div
                  class="score-bar-fill"
                  :style="{
                    width: `${(caseData.final_score ?? 0) * 100}%`,
                    background: scoreColor(caseData.final_score)
                  }"
                />
                <div class="threshold-marker" style="left: 30%"><span>0.3</span></div>
                <div class="threshold-marker" style="left: 60%"><span>0.6</span></div>
                <div class="threshold-marker" style="left: 80%"><span>0.8</span></div>
              </div>
              <div class="score-bar-labels">
                <span>Allow</span>
                <span>Warn</span>
                <span>Quarantine</span>
                <span>Block</span>
              </div>
            </div>
            <!-- Sub-scores -->
            <div class="sub-scores">
              <div class="sub-score" v-if="heuristicAnalysis">
                <span class="sub-label">Heuristic</span>
                <span class="sub-value" :style="{ color: scoreColor(heuristicAnalysis.score) }">
                  {{ formatScore(heuristicAnalysis.score) }}
                </span>
                <span class="sub-time">{{ formatMs(heuristicAnalysis.execution_time_ms) }}</span>
              </div>
              <div class="sub-score" v-if="mlAnalysis">
                <span class="sub-label">ML Classifier</span>
                <span class="sub-value" :style="{ color: scoreColor(mlAnalysis.score) }">
                  {{ formatScore(mlAnalysis.score) }}
                </span>
                <span class="sub-time">{{ formatMs(mlAnalysis.execution_time_ms) }}</span>
              </div>
              <div class="sub-score">
                <span class="sub-label">Pipeline Duration</span>
                <span class="sub-value">{{ formatMs(caseData.pipeline_duration_ms) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div v-if="caseData.status !== 'resolved'" class="card action-prompt">
          <div class="action-prompt-content">
            <div class="action-prompt-text">
              <span class="material-symbols-rounded action-prompt-icon">gavel</span>
              <div>
                <h3>Ready to take action?</h3>
                <p>Review the analysis above, then resolve this case with a final verdict.</p>
              </div>
            </div>
            <button class="btn-primary btn-lg" @click="openActionModal">
              <span class="material-symbols-rounded btn-icon">arrow_forward</span>
              Take Action
            </button>
          </div>
        </div>

        <!-- Resolved state -->
        <div v-else class="card resolved-card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">verified</span>
            Case Resolved
          </h3>
          <div class="resolved-info">
            <span class="badge" :class="verdictBadgeClass(caseData.verdict)">{{ capitalize(caseData.verdict ?? '') }}</span>
            <span v-if="caseData.resolved_at" class="resolved-date">{{ formatDate(caseData.resolved_at) }}</span>
          </div>
          <div v-if="caseData.fp_reviews?.length" class="resolved-fp">
            <span class="material-symbols-rounded" style="font-size: 14px; color: var(--text-muted);">flag</span>
            <span class="resolved-fp-text">Marked as false positive</span>
          </div>
        </div>

      <!-- Action Modal -->
      <Teleport to="body">
        <div v-if="showActionModal" class="modal-overlay" @click.self="closeActionModal">
          <div class="modal">
            <div class="modal-header">
              <h2>Resolve Case #{{ caseData.case_number }}</h2>
              <button class="modal-close" @click="closeActionModal">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>

            <!-- Step indicators -->
            <div class="modal-steps">
              <div class="step-dot" :class="{ active: actionStep >= 1, current: actionStep === 1 }">1</div>
              <div class="step-line" :class="{ active: actionStep >= 2 }" />
              <div class="step-dot" :class="{ active: actionStep >= 2, current: actionStep === 2 }">2</div>
              <div class="step-line" :class="{ active: actionStep >= 3 }" />
              <div class="step-dot" :class="{ active: actionStep >= 3, current: actionStep === 3 }">3</div>
            </div>

            <!-- Step 1: Verdict -->
            <div v-if="actionStep === 1" class="modal-body">
              <h3 class="step-title">Select Verdict</h3>
              <p class="step-desc">What is your final decision for this email?</p>
              <div class="verdict-options">
                <label
                  v-for="v in [
                    { value: 'allowed', label: 'Allow', icon: 'check_circle', color: '#22C55E', desc: 'Email is legitimate, deliver normally' },
                    { value: 'warned', label: 'Warn', icon: 'warning', color: '#F59E0B', desc: 'Deliver with a warning to the recipient' },
                    { value: 'quarantined', label: 'Quarantine', icon: 'shield', color: '#F97316', desc: 'Hold for further review, do not deliver' },
                    { value: 'blocked', label: 'Block', icon: 'block', color: '#EF4444', desc: 'Reject the email entirely' },
                  ]"
                  :key="v.value"
                  class="verdict-option"
                  :class="{ selected: actionVerdict === v.value }"
                  :style="actionVerdict === v.value ? { borderColor: v.color } : {}"
                >
                  <input type="radio" v-model="actionVerdict" :value="v.value" class="sr-only" />
                  <span class="material-symbols-rounded" :style="{ color: v.color }">{{ v.icon }}</span>
                  <div>
                    <span class="verdict-option-label">{{ v.label }}</span>
                    <span class="verdict-option-desc">{{ v.desc }}</span>
                  </div>
                </label>
              </div>
            </div>

            <!-- Step 2: False Positive -->
            <div v-if="actionStep === 2" class="modal-body">
              <h3 class="step-title">False Positive Check</h3>
              <p class="step-desc">Was this email incorrectly flagged by the detection pipeline?</p>
              <label class="fp-toggle">
                <input type="checkbox" v-model="actionIsFP" />
                <span class="fp-toggle-label">Yes, this is a false positive</span>
              </label>
              <div v-if="actionIsFP" class="fp-notes-area">
                <textarea
                  v-model="actionFPNotes"
                  placeholder="Explain why this is a false positive (optional)..."
                  rows="3"
                  class="form-textarea"
                />
                <p class="fp-hint">This feedback helps improve the ML model over time.</p>
              </div>
            </div>

            <!-- Step 3: Confirm -->
            <div v-if="actionStep === 3" class="modal-body">
              <h3 class="step-title">Confirm Action</h3>
              <div class="confirm-summary">
                <div class="confirm-row">
                  <span class="confirm-label">Verdict</span>
                  <span class="badge" :class="verdictBadgeClass(actionVerdict)">{{ capitalize(actionVerdict) }}</span>
                </div>
                <div class="confirm-row">
                  <span class="confirm-label">False Positive</span>
                  <span>{{ actionIsFP ? 'Yes' : 'No' }}</span>
                </div>
                <div v-if="actionIsFP && actionFPNotes" class="confirm-row">
                  <span class="confirm-label">FP Notes</span>
                  <span class="confirm-notes">{{ actionFPNotes }}</span>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="modal-footer">
              <button v-if="actionStep > 1" class="btn-outline-action" @click="actionStep--">
                Back
              </button>
              <div class="modal-footer-right">
                <button class="btn-outline-action" @click="closeActionModal">Cancel</button>
                <button
                  v-if="actionStep < 3"
                  class="btn-primary"
                  :disabled="actionStep === 1 && !actionVerdict"
                  @click="actionStep++"
                >
                  Next
                </button>
                <button
                  v-else
                  class="btn-primary"
                  :disabled="actionSubmitting"
                  @click="submitAction"
                >
                  {{ actionSubmitting ? 'Resolving...' : 'Confirm & Resolve' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
      </div>

      <!-- ============================================================ -->
      <!-- TAB 2: Email Content -->
      <!-- ============================================================ -->
      <div v-if="activeTab === 'email'" class="tab-content">
        <!-- Headers -->
        <div class="card">
          <div class="card-title clickable" @click="showHeaders = !showHeaders">
            <span class="material-symbols-rounded">{{ showHeaders ? 'expand_less' : 'expand_more' }}</span>
            Email Headers
            <span class="header-count" v-if="caseData.email?.headers">
              ({{ Object.keys(caseData.email.headers).length }} headers)
            </span>
          </div>
          <div v-if="showHeaders && caseData.email?.headers" class="headers-list">
            <div v-for="(value, key) in caseData.email.headers" :key="String(key)" class="header-item">
              <span class="header-key">{{ key }}</span>
              <span class="header-value">{{ value }}</span>
            </div>
          </div>
        </div>

        <!-- Body -->
        <div class="card">
          <div class="card-title clickable" @click="showBody = !showBody">
            <span class="material-symbols-rounded">{{ showBody ? 'expand_less' : 'expand_more' }}</span>
            Email Body
          </div>
          <template v-if="showBody">
            <div v-if="caseData.email?.body_html" class="email-body-html">
              <iframe
                :srcdoc="caseData.email.body_html"
                sandbox=""
                class="email-iframe"
              />
            </div>
            <pre v-else-if="caseData.email?.body_text" class="email-body-text">{{ caseData.email.body_text }}</pre>
            <p v-else class="empty-text">No email body available</p>
          </template>
        </div>

        <!-- URLs -->
        <div v-if="caseData.email?.urls?.length" class="card">
          <div class="card-title clickable" @click="showUrls = !showUrls">
            <span class="material-symbols-rounded">{{ showUrls ? 'expand_less' : 'expand_more' }}</span>
            Extracted URLs ({{ caseData.email.urls.length }})
          </div>
          <div v-if="showUrls" class="urls-list">
            <div v-for="(url, i) in caseData.email.urls" :key="i" class="url-item">
              <span class="material-symbols-rounded url-icon">link</span>
              <span class="url-text">{{ url }}</span>
            </div>
          </div>
        </div>

        <!-- Attachments -->
        <div v-if="caseData.email?.attachments?.length" class="card">
          <div class="card-title clickable" @click="showAttachments = !showAttachments">
            <span class="material-symbols-rounded">{{ showAttachments ? 'expand_less' : 'expand_more' }}</span>
            Attachments ({{ caseData.email.attachments.length }})
          </div>
          <div v-if="showAttachments" class="attachments-list">
            <div v-for="(att, i) in caseData.email.attachments" :key="i" class="attachment-item">
              <span class="material-symbols-rounded">description</span>
              <span>{{ (att as Record<string, unknown>).filename ?? `Attachment ${i + 1}` }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================ -->
      <!-- TAB 3: Pipeline Results -->
      <!-- ============================================================ -->
      <div v-if="activeTab === 'pipeline'" class="tab-content">

        <!-- ── Pipeline Timeline ── -->
        <div class="pipeline-timeline">
          <div class="tl-header">
            <span class="material-symbols-rounded tl-header-icon">conversion_path</span>
            <div>
              <h3 class="tl-header-title">Detection Pipeline</h3>
              <p class="tl-header-sub">
                3-stage sequential analysis
                <span v-if="caseData.pipeline_duration_ms" class="tl-duration">
                  — completed in {{ formatMs(caseData.pipeline_duration_ms) }}
                </span>
              </p>
            </div>
          </div>

          <!-- Timeline track -->
          <div class="tl-track">
            <template v-for="(analysis, idx) in caseData.analyses" :key="'tl-' + analysis.id">
              <div class="tl-node" :class="{ 'tl-node-active': analysis.score !== null || analysis.explanation }">
                <div class="tl-node-dot" :style="{ borderColor: stageStatusColor(analysis) }">
                  <span class="material-symbols-rounded" :style="{ color: stageStatusColor(analysis) }">
                    {{ stageIcons[analysis.stage] ?? 'analytics' }}
                  </span>
                </div>
                <div class="tl-node-info">
                  <span class="tl-node-name">{{ stageNames[analysis.stage] ?? analysis.stage }}</span>
                  <span class="tl-node-result" :style="{ color: stageStatusColor(analysis) }">
                    {{ isStageUnavailable(analysis)
                      ? 'Unavailable'
                      : analysis.stage === 'llm'
                        ? stageStatusLabel(analysis)
                        : analysis.score !== null ? (analysis.score * 100).toFixed(0) + '%' : '—' }}
                  </span>
                </div>
                <span v-if="analysis.execution_time_ms" class="tl-node-time">{{ formatMs(analysis.execution_time_ms) }}</span>
              </div>
              <div v-if="idx < caseData.analyses.length - 1" class="tl-connector">
                <span class="material-symbols-rounded tl-arrow">arrow_forward</span>
              </div>
            </template>
            <!-- Final verdict node -->
            <div class="tl-connector">
              <span class="material-symbols-rounded tl-arrow">arrow_forward</span>
            </div>
            <div class="tl-node tl-node-verdict">
              <div class="tl-node-dot tl-dot-verdict" :style="{ borderColor: scoreColor(caseData.final_score) }">
                <span class="material-symbols-rounded" :style="{ color: scoreColor(caseData.final_score) }">verified</span>
              </div>
              <div class="tl-node-info">
                <span class="tl-node-name">Final Verdict</span>
                <span class="tl-node-result" :style="{ color: scoreColor(caseData.final_score) }">
                  {{ formatScore(caseData.final_score) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Stage Detail Cards ── -->
        <div class="pipeline-stages-v2">
          <div v-for="(analysis, idx) in caseData.analyses" :key="analysis.id" class="stage-v2">
            <!-- Left rail -->
            <div class="stage-rail">
              <div class="stage-rail-dot" :style="{ background: stageStatusColor(analysis) }">
                {{ idx + 1 }}
              </div>
              <div v-if="idx < caseData.analyses.length - 1" class="stage-rail-line" />
            </div>

            <!-- Content -->
            <div class="stage-content">
              <div class="stage-v2-header" :class="{ 'stage-v2-disabled': isStageUnavailable(analysis) }" @click="!isStageUnavailable(analysis) && toggleStage(analysis.id)">
                <span class="material-symbols-rounded stage-v2-icon">{{ stageIcons[analysis.stage] ?? 'analytics' }}</span>
                <div class="stage-v2-title">
                  <span class="stage-v2-name">{{ stageNames[analysis.stage] ?? analysis.stage }}</span>
                  <span class="stage-v2-desc">{{ stageDescs[analysis.stage] ?? '' }}</span>
                </div>
                <div class="stage-v2-metrics">
                  <template v-if="isStageUnavailable(analysis)">
                    <span
                      class="stage-v2-unavailable tooltip-wrap tooltip-bottom tooltip-right"
                      :data-tooltip="`${stageNames[analysis.stage] ?? analysis.stage} was not executed during this analysis pipeline run.`"
                    >Unavailable</span>
                  </template>
                  <template v-else>
                    <span v-if="analysis.score !== null" class="stage-v2-score" :style="{ color: scoreColor(analysis.score) }">
                      {{ (analysis.score * 100).toFixed(0) }}%
                    </span>
                    <span v-if="analysis.confidence !== null" class="stage-v2-conf">
                      {{ (analysis.confidence * 100).toFixed(0) }}% conf
                    </span>
                    <span class="stage-v2-time">{{ formatMs(analysis.execution_time_ms) }}</span>
                  </template>
                  <span v-if="!isStageUnavailable(analysis)" class="material-symbols-rounded stage-v2-toggle">
                    {{ expandedStages.has(analysis.id) ? 'expand_less' : 'expand_more' }}
                  </span>
                </div>
              </div>

              <!-- Score bar -->
              <div v-if="expandedStages.has(analysis.id) && analysis.score !== null" class="stage-v2-bar">
                <div class="mini-bar-track">
                  <div
                    class="mini-bar-fill"
                    :style="{ width: `${analysis.score * 100}%`, background: scoreColor(analysis.score) }"
                  />
                </div>
              </div>

              <!-- Heuristic sub-scores -->
              <div v-if="expandedStages.has(analysis.id) && analysis.stage === 'heuristic' && analysis.metadata" class="stage-v2-subs">
                <div v-if="analysis.metadata.domain_score !== undefined" class="hsub-item">
                  <span class="hsub-label">Domain</span>
                  <span class="hsub-value" :style="{ color: scoreColor(Number(analysis.metadata.domain_score)) }">
                    {{ (Number(analysis.metadata.domain_score) * 100).toFixed(0) }}%
                  </span>
                </div>
                <div v-if="analysis.metadata.url_score !== undefined" class="hsub-item">
                  <span class="hsub-label">URL</span>
                  <span class="hsub-value" :style="{ color: scoreColor(Number(analysis.metadata.url_score)) }">
                    {{ (Number(analysis.metadata.url_score) * 100).toFixed(0) }}%
                  </span>
                </div>
                <div v-if="analysis.metadata.keyword_score !== undefined" class="hsub-item">
                  <span class="hsub-label">Keyword</span>
                  <span class="hsub-value" :style="{ color: scoreColor(Number(analysis.metadata.keyword_score)) }">
                    {{ (Number(analysis.metadata.keyword_score) * 100).toFixed(0) }}%
                  </span>
                </div>
                <div v-if="analysis.metadata.auth_score !== undefined" class="hsub-item">
                  <span class="hsub-label">Auth</span>
                  <span class="hsub-value" :style="{ color: scoreColor(Number(analysis.metadata.auth_score)) }">
                    {{ (Number(analysis.metadata.auth_score) * 100).toFixed(0) }}%
                  </span>
                </div>
              </div>

              <!-- ML model info -->
              <div v-if="expandedStages.has(analysis.id) && analysis.stage === 'ml' && analysis.metadata?.model_version" class="stage-v2-ml">
                <span class="badge badge-info">v{{ analysis.metadata.model_version }}</span>
              </div>

              <!-- LLM explanation -->
              <p v-if="expandedStages.has(analysis.id) && analysis.explanation" class="stage-v2-explanation">{{ analysis.explanation }}</p>

              <!-- Evidences -->
              <div v-if="expandedStages.has(analysis.id) && analysis.evidences?.length" class="stage-v2-evidences">
                <h5 class="evidence-title">Evidence ({{ analysis.evidences.length }})</h5>
                <div v-for="ev in sortedEvidences(analysis.evidences)" :key="ev.id" class="evidence-item">
                  <span class="badge" :class="severityBadgeClass(ev.severity)">{{ ev.severity }}</span>
                  <span class="evidence-type">{{ evidenceLabel(ev.type) }}</span>
                  <p class="evidence-desc">{{ ev.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Final Verdict ── -->
        <div class="verdict-v2">
          <div class="verdict-v2-left">
            <div class="verdict-v2-ring">
              <svg viewBox="0 0 80 80" class="score-svg">
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--border-color)" stroke-width="5" />
                <circle
                  cx="40" cy="40" r="34" fill="none"
                  :stroke="scoreColor(caseData.final_score)"
                  stroke-width="5"
                  stroke-linecap="round"
                  :stroke-dasharray="`${(caseData.final_score ?? 0) * 213.6} 213.6`"
                  transform="rotate(-90 40 40)"
                />
              </svg>
              <div class="score-ring-text">
                <span class="score-ring-value" :style="{ color: scoreColor(caseData.final_score) }">
                  {{ caseData.final_score !== null ? (caseData.final_score * 100).toFixed(0) : '—' }}
                </span>
              </div>
            </div>
          </div>
          <div class="verdict-v2-details">
            <div class="verdict-row">
              <span class="verdict-label">Risk Level</span>
              <span class="badge" :class="riskBadgeClass(caseData.risk_level)">
                {{ caseData.risk_level ? capitalize(caseData.risk_level) : '—' }}
              </span>
            </div>
            <div class="verdict-row">
              <span class="verdict-label">Verdict</span>
              <span class="badge" :class="verdictBadgeClass(caseData.verdict)">
                {{ caseData.verdict ? capitalize(caseData.verdict) : '—' }}
              </span>
            </div>
            <div class="verdict-row">
              <span class="verdict-label">Threat Category</span>
              <span v-if="caseData.threat_category && threatCategoryMeta[caseData.threat_category]"
                class="category-badge"
                :style="{
                  color: threatCategoryMeta[caseData.threat_category].color,
                  background: threatCategoryMeta[caseData.threat_category].bg,
                }"
              >{{ threatCategoryMeta[caseData.threat_category].label }}</span>
              <span v-else>{{ caseData.threat_category ? capitalize(caseData.threat_category.replace(/_/g, ' ')) : '—' }}</span>
            </div>
            <div class="verdict-row">
              <span class="verdict-label">Pipeline Duration</span>
              <span class="verdict-duration">{{ formatMs(caseData.pipeline_duration_ms) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================ -->
      <!-- Notes (always visible) -->
      <!-- ============================================================ -->
      <div class="card notes-section">
        <h3 class="card-title">
          <span class="material-symbols-rounded">note</span>
          Notes ({{ caseData.notes?.length ?? 0 }})
        </h3>
        <div v-if="caseData.notes?.length" class="notes-list">
          <div v-for="note in caseData.notes" :key="note.id" class="note-item">
            <div class="note-meta">
              <span class="note-author">{{ note.author_name ?? 'Unknown' }}</span>
              <div class="note-meta-right">
                <span class="note-date">{{ formatDate(note.created_at) }}</span>
                <button
                  v-if="editingNoteId !== note.id"
                  class="note-edit-btn"
                  title="Edit note"
                  @click="startEditNote(note)"
                >
                  <span class="material-symbols-rounded">edit</span>
                </button>
              </div>
            </div>
            <template v-if="editingNoteId === note.id">
              <textarea
                v-model="editingNoteContent"
                rows="2"
                class="form-textarea note-edit-textarea"
              />
              <div class="note-edit-actions">
                <button class="btn-primary btn-sm" @click="handleUpdateNote(note)">Save</button>
                <button class="btn-outline-action btn-sm" @click="cancelEditNote">Cancel</button>
              </div>
            </template>
            <p v-else>{{ note.content }}</p>
          </div>
        </div>
        <p v-else class="empty-text">No notes yet.</p>
        <div class="add-note">
          <textarea
            v-model="newNote"
            placeholder="Add a note..."
            rows="2"
            class="form-textarea"
          />
          <button
            class="btn-primary"
            :disabled="!newNote.trim() || addingNote"
            @click="handleAddNote"
          >{{ addingNote ? 'Adding...' : 'Add Note' }}</button>
        </div>
      </div>
    </template>

    <!-- Not found -->
    <div v-else class="error-state">
      <p>Case not found</p>
    </div>
  </div>
</template>

<style scoped>
.case-detail {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  max-width: 1200px;
  font-family: var(--font-mono);
}

/* Loading / Error */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 64px;
  color: var(--text-secondary);
  font-size: var(--font-md);
  font-family: var(--font-mono);
}

.spin {
  font-size: 32px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Header */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 4px;
  padding: 0;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.15s;
}

.btn-back:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
  border-color: var(--text-muted);
}

.btn-back .material-symbols-rounded {
  font-size: 18px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-info h1 {
  font-family: var(--font-mono);
  font-size: var(--font-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-badges {
  display: flex;
  gap: 6px;
}

.header-score {
  display: flex;
  align-items: center;
}

.score-ring {
  position: relative;
  width: 72px;
  height: 72px;
}

.score-svg {
  width: 100%;
  height: 100%;
}

.score-arc {
  animation: score-fill 1s ease-out forwards;
}

@keyframes score-fill {
  from {
    stroke-dashoffset: 213.6;
  }
  to {
    stroke-dashoffset: 0;
  }
}

.score-ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-ring-value {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
}

.score-ring-label {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 1px;
}

/* Badges */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  font-weight: 600;
  text-transform: capitalize;
}

.badge-success { color: var(--color-success); background: var(--color-success-bg); }
.badge-warn { color: var(--color-warn); background: var(--color-warn-bg); }
.badge-high { color: var(--color-high); background: var(--color-high-bg); }
.badge-critical { color: var(--color-critical); background: var(--color-critical-bg); }
.badge-info { color: var(--color-info); background: var(--color-info-bg); }
.badge-muted { color: var(--text-muted); background: rgba(107, 114, 128, 0.12); }

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: var(--font-base);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.tab-btn:hover {
  color: var(--text-secondary);
}

.tab-btn.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
}

.tab-btn .material-symbols-rounded {
  font-size: 18px;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Card */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.card:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.card-title .material-symbols-rounded {
  font-size: 18px;
  color: var(--accent-cyan);
}

.card-title.clickable {
  cursor: pointer;
  user-select: none;
}

.card-title.clickable:hover {
  color: var(--accent-cyan);
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.info-label {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-primary);
  word-break: break-word;
}

/* Category Badge */
.category-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  font-weight: 600;
  cursor: help;
}

/* CSS Tooltips */
.tooltip-wrap {
  position: relative;
  cursor: help;
}

.tooltip-wrap::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-elevated);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  font-weight: 400;
  line-height: 1.5;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  white-space: normal;
  width: 260px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.tooltip-wrap:hover::after {
  opacity: 1;
}

.tooltip-bottom::after {
  bottom: auto;
  top: calc(100% + 8px);
}

.tooltip-right::after {
  left: auto;
  right: 0;
  transform: none;
}

/* LLM Explanation */
.llm-explanation {
  font-family: var(--font-family);
  font-size: var(--font-base);
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
}

.llm-meta {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
}

/* Auth Badges */
.auth-badges {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.auth-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  min-width: 140px;
}

.auth-pass {
  background: var(--color-success-bg);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.auth-fail {
  background: var(--color-critical-bg);
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.auth-icon {
  font-size: 20px;
}

.auth-pass .auth-icon { color: var(--color-success); }
.auth-fail .auth-icon { color: var(--color-critical); }

.auth-name {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  font-weight: 600;
  color: var(--text-primary);
}

.auth-result {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-left: auto;
  text-transform: uppercase;
}

.auth-help {
  font-size: 14px;
  color: var(--text-muted);
  margin-left: 4px;
  opacity: 0.5;
  cursor: help;
}

/* Score Summary */
.score-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.score-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.score-big {
  font-family: var(--font-mono);
  font-size: var(--font-3xl);
  font-weight: 800;
}

.score-desc {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-muted);
}

/* Score Bar */
.score-bar-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-bar-track {
  height: 10px;
  background: var(--border-color);
  border-radius: 5px;
  overflow: visible;
  position: relative;
}

.score-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.4s ease;
}

.threshold-marker {
  position: absolute;
  top: -4px;
  bottom: -4px;
  width: 1px;
  background: var(--text-dim);
}

.threshold-marker span {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
}

.score-bar-labels {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  padding-top: 4px;
}

/* Sub-scores */
.sub-scores {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.sub-score {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--bg-elevated);
  border-radius: 6px;
}

.sub-label {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.sub-value {
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 700;
}

.sub-time {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
}

/* Action Prompt */
.action-prompt-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.action-prompt-text {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-prompt-icon {
  font-size: 28px;
  color: var(--accent-cyan);
}

.action-prompt-text h3 {
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.action-prompt-text p {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
  margin: 2px 0 0 0;
}

.btn-lg {
  padding: 10px 24px;
  font-size: var(--font-md);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 520px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.modal-header h2 {
  font-family: var(--font-mono);
  font-size: var(--font-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.modal-close:hover {
  color: var(--text-primary);
}

/* Steps */
.modal-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 20px 24px 8px;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  font-weight: 700;
  background: var(--bg-elevated);
  color: var(--text-muted);
  border: 2px solid var(--border-color);
  transition: all 0.2s;
}

.step-dot.active {
  background: var(--accent-cyan);
  color: #0A1628;
  border-color: var(--accent-cyan);
}

.step-dot.current {
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.2);
}

.step-line {
  width: 48px;
  height: 2px;
  background: var(--border-color);
  transition: background 0.2s;
}

.step-line.active {
  background: var(--accent-cyan);
}

.modal-body {
  padding: 20px 24px;
}

.step-title {
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.step-desc {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-muted);
  margin: 0 0 16px 0;
}

/* Verdict Options */
.verdict-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.verdict-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-elevated);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.verdict-option:hover {
  border-color: var(--text-muted);
}

.verdict-option.selected {
  background: rgba(0, 212, 255, 0.05);
}

.verdict-option .material-symbols-rounded {
  font-size: 22px;
}

.verdict-option-label {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 600;
  color: var(--text-primary);
}

.verdict-option-desc {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

/* FP Toggle */
.fp-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-elevated);
  border-radius: 8px;
  cursor: pointer;
}

.fp-toggle input {
  accent-color: var(--accent-cyan);
  width: 16px;
  height: 16px;
}

.fp-toggle-label {
  font-family: var(--font-mono);
  font-size: var(--font-md);
  color: var(--text-primary);
}

.fp-notes-area {
  margin-top: 12px;
}

.fp-hint {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin: 6px 0 0 0;
}

/* Confirm */
.confirm-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-elevated);
  border-radius: 8px;
}

.confirm-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.confirm-label {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-muted);
}

.confirm-notes {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  text-align: right;
  max-width: 280px;
}

/* Modal Footer */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-color);
}

.modal-footer-right {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.resolved-fp {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.resolved-fp-text {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
}

.btn-icon {
  font-size: 16px;
}

.btn-outline-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  padding: 8px 16px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: var(--font-base);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-outline-action:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.btn-outline-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Resolved State */
.resolved-card {
  border-color: var(--color-success);
  border-style: solid;
}

.resolved-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.resolved-date {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
}

.form-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.form-select {
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-base);
  min-width: 200px;
}

.form-textarea {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-base);
  resize: vertical;
  margin-top: 8px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--accent-cyan);
  color: #0A1628;
  border: none;
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: var(--font-base);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-cyan-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Email Content Tab */
.header-count {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
  font-weight: 400;
}

.headers-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.header-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
  font-family: var(--font-mono);
  font-size: var(--font-sm);
}

.header-key {
  color: var(--accent-cyan);
  font-weight: 600;
  min-width: 140px;
  flex-shrink: 0;
}

.header-value {
  color: var(--text-secondary);
  word-break: break-all;
}

.email-body-html {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.email-iframe {
  width: 100%;
  min-height: 400px;
  border: none;
  background: #fff;
}

.email-body-text {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--bg-elevated);
  padding: 16px;
  border-radius: var(--border-radius);
  max-height: 500px;
  overflow-y: auto;
  margin: 0;
}

.urls-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.url-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: 6px;
}

.url-icon {
  font-size: 16px;
  color: var(--text-muted);
}

.url-text {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--accent-cyan);
  word-break: break-all;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-secondary);
}

.attachment-item .material-symbols-rounded {
  font-size: 18px;
  color: var(--text-muted);
}

/* ── Pipeline Timeline ── */
.pipeline-timeline {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--space-lg);
  transition: border-color 0.3s, box-shadow 0.3s;
}

.pipeline-timeline:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}

.tl-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.tl-header-icon {
  font-size: 24px;
  color: var(--accent-cyan);
}

.tl-header-title {
  font-family: var(--font-mono);
  font-size: var(--font-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.tl-header-sub {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
  margin: 2px 0 0 0;
}

.tl-duration {
  color: var(--text-secondary);
}

.tl-track {
  display: flex;
  align-items: center;
  gap: 0;
  overflow-x: auto;
  padding: 4px 0;
}

.tl-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 120px;
  flex-shrink: 0;
}

.tl-node-dot {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  background: var(--bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.tl-node-active .tl-node-dot {
  background: rgba(0, 212, 255, 0.06);
}

.tl-node-dot .material-symbols-rounded {
  font-size: 22px;
}

.tl-node-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.tl-node-name {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.tl-node-result {
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 800;
}

.tl-node-time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

.tl-connector {
  flex: 1;
  min-width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  margin-top: 22px;
}

.tl-arrow {
  font-size: 18px;
  color: var(--text-muted);
}

.tl-dot-verdict {
  border-width: 2px;
}

/* ── Stage Detail Cards v2 ── */
.pipeline-stages-v2 {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.stage-v2 {
  display: flex;
  gap: 0;
}

.stage-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
  flex-shrink: 0;
}

.stage-rail-dot {
  width: 26px;
  height: 26px;
  border-radius: 13px;
  color: #0A1628;
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 18px;
}

.stage-rail-line {
  width: 2px;
  flex: 1;
  background: var(--border-color);
  margin: 4px 0;
}

.stage-content {
  flex: 1;
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 18px 20px;
  margin: 6px 0 6px 12px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.stage-content:hover {
  border-color: rgba(0, 212, 255, 0.12);
  box-shadow: var(--glow-cyan);
}

.stage-v2-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.stage-v2-header:not(.stage-v2-disabled):hover .stage-v2-name {
  color: var(--accent-cyan);
}

.stage-v2-disabled {
  cursor: default;
}

.stage-v2-toggle {
  font-size: 20px;
  color: var(--text-muted);
  margin-left: 4px;
}

.stage-v2-icon {
  font-size: 20px;
  color: var(--accent-cyan);
  margin-top: 1px;
}

.stage-v2-title {
  flex: 1;
  min-width: 0;
}

.stage-v2-name {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--font-md);
  font-weight: 700;
  color: var(--text-primary);
}

.stage-v2-desc {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin-top: 1px;
  line-height: 1.4;
}

.stage-v2-metrics {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.stage-v2-score {
  font-family: var(--font-mono);
  font-size: var(--font-lg);
  font-weight: 800;
}

.stage-v2-conf {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
  background: var(--color-info-bg);
  padding: 2px 8px;
  border-radius: 10px;
}

.stage-v2-time {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
}

.stage-v2-unavailable {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-muted);
  font-style: italic;
}

.stage-v2-bar {
  margin: 12px 0 0 30px;
}

.mini-bar-track {
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
}

.mini-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.stage-v2-subs {
  display: flex;
  gap: 12px;
  margin: 12px 0 0 30px;
  flex-wrap: wrap;
}

.hsub-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg-elevated);
  border-radius: 4px;
}

.hsub-label {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.hsub-value {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  font-weight: 700;
}

.stage-v2-ml {
  margin: 10px 0 0 30px;
}

.stage-v2-explanation {
  font-family: var(--font-family);
  font-size: var(--font-base);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 12px 0 0 30px;
  white-space: pre-wrap;
}

.stage-v2-evidences {
  margin: 12px 0 0 30px;
}

.evidence-title {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.evidence-item {
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: 6px;
  margin-bottom: 6px;
}

.evidence-type {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
  text-transform: capitalize;
  margin-left: 6px;
}

.evidence-desc {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 4px 0 0 0;
  line-height: 1.4;
}

/* ── Final Verdict v2 ── */
.verdict-v2 {
  display: flex;
  gap: 32px;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--accent-cyan);
  border-radius: var(--border-radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--glow-cyan);
}

.verdict-v2-left {
  flex-shrink: 0;
}

.verdict-v2-ring {
  position: relative;
  width: 80px;
  height: 80px;
}

.verdict-v2-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.verdict-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.verdict-label {
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  color: var(--text-muted);
  min-width: 120px;
}

.verdict-duration {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  font-weight: 500;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

/* Notes Section */
.notes-section {
  margin-top: 8px;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.note-item {
  padding: 10px 12px;
  background: var(--bg-elevated);
  border-radius: 6px;
}

.note-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin-bottom: 4px;
}

.note-meta-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.note-edit-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
}

.note-item:hover .note-edit-btn {
  opacity: 1;
}

.note-edit-btn:hover {
  color: var(--accent-cyan);
}

.note-edit-btn .material-symbols-rounded {
  font-size: 14px;
}

.note-edit-textarea {
  margin-top: 4px;
}

.note-edit-actions {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: var(--font-sm);
}

.note-author {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--text-secondary);
}

.note-item p {
  font-family: var(--font-mono);
  font-size: var(--font-base);
  color: var(--text-secondary);
  margin: 0;
}

.add-note {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.empty-text {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: var(--font-base);
}
</style>
