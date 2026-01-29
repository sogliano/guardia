<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { CaseDetail, Analysis, Evidence, CaseNote } from '@/types/case'
import { fetchCaseDetail, addCaseNote, resolveCase, createFPReview } from '@/services/caseService'
import { scoreColor } from '@/utils/colors'

const route = useRoute()
const router = useRouter()
const caseId = route.params.id as string

const caseData = ref<CaseDetail | null>(null)
const loading = ref(true)
const error = ref('')
const activeTab = ref<'overview' | 'email' | 'pipeline'>('overview')

// Resolve form
const resolveVerdict = ref('')
const resolving = ref(false)

// Note form
const newNote = ref('')
const addingNote = ref(false)

// FP Review form
const fpDecision = ref('')
const fpNotes = ref('')
const submittingFP = ref(false)

// Email headers toggle
const showHeaders = ref(false)

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
  return score != null ? (score * 100).toFixed(1) + '%' : '—'
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
    color: '#22C55E',
    bg: 'rgba(34, 197, 94, 0.15)',
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

async function handleResolve() {
  if (!resolveVerdict.value || !caseData.value) return
  resolving.value = true
  try {
    await resolveCase(caseId, resolveVerdict.value)
    await loadData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to resolve'
  } finally {
    resolving.value = false
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

async function handleFPReview() {
  if (!fpDecision.value) return
  submittingFP.value = true
  try {
    await createFPReview(caseId, {
      decision: fpDecision.value,
      notes: fpNotes.value || undefined,
    })
    fpDecision.value = ''
    fpNotes.value = ''
    await loadData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to submit FP review'
  } finally {
    submittingFP.value = false
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
          Back
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
                {{ (caseData.final_score * 100).toFixed(0) }}
              </span>
              <span class="score-ring-label">Score</span>
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
                  class="category-badge"
                  :style="{
                    color: threatCategoryMeta[caseData.threat_category].color,
                    background: threatCategoryMeta[caseData.threat_category].bg,
                  }"
                  :title="threatCategoryMeta[caseData.threat_category].desc"
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
              class="auth-badge"
              :class="authBadgeClass(authResults.spf)"
              title="SPF (Sender Policy Framework): Verifica que el servidor que envió el email está autorizado por el dominio del remitente. PASS = autorizado, FAIL/SOFTFAIL = no autorizado."
            >
              <span class="material-symbols-rounded auth-icon">
                {{ authResults.spf === 'pass' ? 'check_circle' : 'cancel' }}
              </span>
              <span class="auth-name">SPF</span>
              <span class="auth-result">{{ authResults.spf }}</span>
              <span class="material-symbols-rounded auth-help">help</span>
            </div>
            <div
              class="auth-badge"
              :class="authBadgeClass(authResults.dkim)"
              title="DKIM (DomainKeys Identified Mail): Verifica la integridad del email mediante firma digital. PASS = no fue alterado en tránsito, FAIL = posible manipulación."
            >
              <span class="material-symbols-rounded auth-icon">
                {{ authResults.dkim === 'pass' ? 'check_circle' : 'cancel' }}
              </span>
              <span class="auth-name">DKIM</span>
              <span class="auth-result">{{ authResults.dkim }}</span>
              <span class="material-symbols-rounded auth-help">help</span>
            </div>
            <div
              class="auth-badge"
              :class="authBadgeClass(authResults.dmarc)"
              title="DMARC (Domain-based Message Authentication): Política del dominio que combina SPF y DKIM. PASS = cumple la política, FAIL = no cumple, posible suplantación de identidad."
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
        <div v-if="caseData.status !== 'resolved'" class="actions-grid">
          <!-- Resolve Case -->
          <div class="card action-card">
            <h3 class="card-title">
              <span class="material-symbols-rounded">gavel</span>
              Resolve Case
            </h3>
            <p class="action-desc">Select a final verdict for this case. This will close the case and mark it as resolved.</p>
            <div class="form-row">
              <select v-model="resolveVerdict" class="form-select">
                <option value="">Select verdict...</option>
                <option value="allowed">Allowed</option>
                <option value="warned">Warned</option>
                <option value="quarantined">Quarantined</option>
                <option value="blocked">Blocked</option>
              </select>
              <button
                class="btn-primary"
                :disabled="!resolveVerdict || resolving"
                @click="handleResolve"
              >
                <span class="material-symbols-rounded btn-icon">check_circle</span>
                {{ resolving ? 'Resolving...' : 'Resolve' }}
              </button>
            </div>
          </div>

          <!-- FP Review -->
          <div class="card action-card action-card-secondary">
            <h3 class="card-title">
              <span class="material-symbols-rounded">rate_review</span>
              False Positive Review
            </h3>
            <p class="action-desc">Was this email incorrectly flagged? Mark it as a false positive for model improvement.</p>
            <select v-model="fpDecision" class="form-select">
              <option value="">Select decision...</option>
              <option value="confirmed_fp">Confirmed False Positive</option>
              <option value="kept_flagged">Keep Flagged</option>
            </select>
            <textarea
              v-model="fpNotes"
              placeholder="Optional notes..."
              rows="2"
              class="form-textarea"
            />
            <button
              class="btn-outline-action"
              :disabled="!fpDecision || submittingFP"
              @click="handleFPReview"
            >
              <span class="material-symbols-rounded btn-icon">send</span>
              {{ submittingFP ? 'Submitting...' : 'Submit Review' }}
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
        </div>
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
          <h3 class="card-title">
            <span class="material-symbols-rounded">article</span>
            Email Body
          </h3>
          <div v-if="caseData.email?.body_html" class="email-body-html">
            <iframe
              :srcdoc="caseData.email.body_html"
              sandbox=""
              class="email-iframe"
            />
          </div>
          <pre v-else-if="caseData.email?.body_text" class="email-body-text">{{ caseData.email.body_text }}</pre>
          <p v-else class="empty-text">No email body available</p>
        </div>

        <!-- URLs -->
        <div v-if="caseData.email?.urls?.length" class="card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">link</span>
            Extracted URLs ({{ caseData.email.urls.length }})
          </h3>
          <div class="urls-list">
            <div v-for="(url, i) in caseData.email.urls" :key="i" class="url-item">
              <span class="material-symbols-rounded url-icon">link</span>
              <span class="url-text">{{ url }}</span>
            </div>
          </div>
        </div>

        <!-- Attachments -->
        <div v-if="caseData.email?.attachments?.length" class="card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">attach_file</span>
            Attachments ({{ caseData.email.attachments.length }})
          </h3>
          <div class="attachments-list">
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
        <!-- Pipeline Stages -->
        <div class="pipeline-stages">
          <div v-for="(analysis, idx) in caseData.analyses" :key="analysis.id" class="stage-card">
            <div class="stage-header">
              <div class="stage-number">{{ idx + 1 }}</div>
              <span class="material-symbols-rounded stage-icon">{{ stageIcons[analysis.stage] ?? 'analytics' }}</span>
              <span class="stage-name">{{ stageNames[analysis.stage] ?? analysis.stage }}</span>
              <span v-if="analysis.score !== null" class="stage-score" :style="{ color: scoreColor(analysis.score) }">
                {{ (analysis.score * 100).toFixed(0) }}%
              </span>
              <span v-if="analysis.confidence !== null" class="stage-confidence">
                {{ (analysis.confidence * 100).toFixed(0) }}% conf
              </span>
              <span class="stage-time">{{ formatMs(analysis.execution_time_ms) }}</span>
            </div>

            <!-- Score bar for heuristic/ml -->
            <div v-if="analysis.score !== null" class="stage-score-bar">
              <div class="mini-bar-track">
                <div
                  class="mini-bar-fill"
                  :style="{ width: `${analysis.score * 100}%`, background: scoreColor(analysis.score) }"
                />
              </div>
            </div>

            <!-- Heuristic sub-scores -->
            <div v-if="analysis.stage === 'heuristic' && analysis.metadata" class="heuristic-sub">
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
            <div v-if="analysis.stage === 'ml' && analysis.metadata" class="ml-meta">
              <span v-if="analysis.metadata.model_version" class="badge badge-info">
                v{{ analysis.metadata.model_version }}
              </span>
            </div>

            <!-- LLM explanation -->
            <p v-if="analysis.explanation" class="stage-explanation">{{ analysis.explanation }}</p>

            <!-- Evidences for this stage -->
            <div v-if="analysis.evidences?.length" class="stage-evidences">
              <h5 class="evidence-title">Evidence ({{ analysis.evidences.length }})</h5>
              <div v-for="ev in analysis.evidences" :key="ev.id" class="evidence-item">
                <span class="badge" :class="severityBadgeClass(ev.severity)">{{ ev.severity }}</span>
                <span class="evidence-type">{{ ev.type.replace(/_/g, ' ') }}</span>
                <p class="evidence-desc">{{ ev.description }}</p>
              </div>
            </div>

            <!-- Connector -->
            <div v-if="idx < caseData.analyses.length - 1" class="stage-connector" />
          </div>
        </div>

        <!-- Final Verdict Card -->
        <div class="card verdict-card">
          <h3 class="card-title">
            <span class="material-symbols-rounded">verified</span>
            Final Verdict
          </h3>
          <div class="verdict-summary">
            <div class="verdict-score">
              <span class="score-big" :style="{ color: scoreColor(caseData.final_score) }">
                {{ formatScore(caseData.final_score) }}
              </span>
            </div>
            <div class="verdict-details">
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
                <span>{{ caseData.threat_category ? capitalize(caseData.threat_category.replace(/_/g, ' ')) : '—' }}</span>
              </div>
              <div class="verdict-row">
                <span class="verdict-label">Pipeline Duration</span>
                <span>{{ formatMs(caseData.pipeline_duration_ms) }}</span>
              </div>
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
              <span class="note-author">{{ note.author_id.slice(0, 8) }}...</span>
              <span class="note-date">{{ formatDate(note.created_at) }}</span>
            </div>
            <p>{{ note.content }}</p>
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
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1200px;
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
  font-size: 14px;
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
  gap: 4px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}

.btn-back:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.btn-back .material-symbols-rounded {
  font-size: 18px;
}

.header-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-info h1 {
  font-size: 20px;
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

.score-ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-ring-value {
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
}

.score-ring-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-top: 1px;
}

/* Badges */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
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
  font-size: 13px;
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
  border-radius: 8px;
  padding: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
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
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.info-value {
  font-size: 13px;
  color: var(--text-primary);
  word-break: break-word;
}

/* Category Badge */
.category-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: help;
}

/* LLM Explanation */
.llm-explanation {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
}

.llm-meta {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  font-size: 11px;
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
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.auth-result {
  font-size: 12px;
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
  font-size: 32px;
  font-weight: 800;
}

.score-desc {
  font-size: 13px;
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
  font-size: 9px;
  color: var(--text-muted);
}

.score-bar-labels {
  display: flex;
  justify-content: space-between;
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
  font-size: 12px;
  color: var(--text-secondary);
}

.sub-value {
  font-size: 14px;
  font-weight: 700;
}

.sub-time {
  font-size: 11px;
  color: var(--text-muted);
}

/* Actions */
.actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.action-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-card-secondary {
  border-style: dashed;
}

.action-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin: -4px 0 0 0;
  line-height: 1.5;
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
  border-radius: 6px;
  font-size: 13px;
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
  font-size: 12px;
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
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  min-width: 200px;
}

.form-textarea {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
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
  border-radius: 6px;
  font-size: 13px;
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
  font-size: 12px;
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
  font-size: 12px;
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
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--bg-elevated);
  padding: 16px;
  border-radius: 6px;
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
  font-size: 12px;
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
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.attachment-item .material-symbols-rounded {
  font-size: 18px;
  color: var(--text-muted);
}

/* Pipeline Stages */
.pipeline-stages {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.stage-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px 20px;
}

.stage-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stage-number {
  width: 24px;
  height: 24px;
  border-radius: 12px;
  background: var(--accent-cyan);
  color: #0A1628;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stage-icon {
  font-size: 18px;
  color: var(--text-secondary);
}

.stage-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.stage-score {
  font-size: 16px;
  font-weight: 700;
}

.stage-confidence {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--color-info-bg);
  padding: 2px 8px;
  border-radius: 10px;
}

.stage-time {
  font-size: 11px;
  color: var(--text-muted);
}

.stage-score-bar {
  margin: 10px 0 0 34px;
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

/* Heuristic sub-scores */
.heuristic-sub {
  display: flex;
  gap: 16px;
  margin: 10px 0 0 34px;
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
  font-size: 11px;
  color: var(--text-secondary);
}

.hsub-value {
  font-size: 13px;
  font-weight: 700;
}

/* ML meta */
.ml-meta {
  margin: 8px 0 0 34px;
}

/* Stage explanation */
.stage-explanation {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 10px 0 0 34px;
  white-space: pre-wrap;
}

/* Evidence */
.stage-evidences {
  margin: 12px 0 0 34px;
}

.evidence-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.evidence-item {
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: 6px;
  margin-bottom: 6px;
}

.evidence-type {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: capitalize;
  margin-left: 6px;
}

.evidence-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 4px 0 0 0;
  line-height: 1.4;
}

.stage-connector {
  width: 2px;
  height: 16px;
  background: var(--border-color);
  margin: 0 auto;
}

/* Final Verdict */
.verdict-card {
  border-color: var(--accent-cyan);
  border-width: 1px;
}

.verdict-summary {
  display: flex;
  gap: 32px;
  align-items: center;
}

.verdict-score {
  flex-shrink: 0;
}

.verdict-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.verdict-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.verdict-label {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 120px;
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
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.note-item p {
  font-size: 13px;
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
  font-size: 13px;
}
</style>
