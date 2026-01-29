<script setup lang="ts">
import { computed } from 'vue'
import Tag from 'primevue/tag'
import type { Email } from '@/types/email'

const props = defineProps<{
  email: Email
}>()

const authChecks = computed(() => {
  const auth = props.email.auth_results ?? {}
  return Object.entries(auth).map(([key, val]) => ({
    name: key.toUpperCase(),
    value: String(val),
    pass: String(val).toLowerCase() === 'pass',
  }))
})

const urlCount = computed(() => props.email.urls?.length ?? 0)
const attachmentCount = computed(() => props.email.attachments?.length ?? 0)
</script>

<template>
  <div class="email-preview">
    <div class="preview-header">
      <h4 class="preview-title">Email Preview</h4>
    </div>

    <div class="meta-grid">
      <div class="meta-row">
        <span class="meta-label">From</span>
        <span class="meta-value">
          {{ email.sender_name ? `${email.sender_name} <${email.sender_email}>` : email.sender_email }}
        </span>
      </div>
      <div class="meta-row">
        <span class="meta-label">To</span>
        <span class="meta-value">{{ email.recipient_email }}</span>
      </div>
      <div v-if="email.reply_to" class="meta-row">
        <span class="meta-label">Reply-To</span>
        <span class="meta-value suspicious">{{ email.reply_to }}</span>
      </div>
      <div class="meta-row">
        <span class="meta-label">Subject</span>
        <span class="meta-value subject">{{ email.subject ?? '(no subject)' }}</span>
      </div>
      <div class="meta-row">
        <span class="meta-label">Message ID</span>
        <span class="meta-value mono">{{ email.message_id }}</span>
      </div>
    </div>

    <div v-if="authChecks.length" class="auth-section">
      <span class="section-label">Authentication</span>
      <div class="auth-tags">
        <Tag
          v-for="c in authChecks"
          :key="c.name"
          :value="`${c.name}: ${c.value}`"
          :severity="c.pass ? 'success' : 'danger'"
        />
      </div>
    </div>

    <div class="stats-row">
      <span class="stat">
        <span class="material-symbols-rounded stat-icon">link</span>
        {{ urlCount }} URL{{ urlCount !== 1 ? 's' : '' }}
      </span>
      <span class="stat">
        <span class="material-symbols-rounded stat-icon">attach_file</span>
        {{ attachmentCount }} attachment{{ attachmentCount !== 1 ? 's' : '' }}
      </span>
    </div>

    <div v-if="email.body_text" class="body-preview">
      <span class="section-label">Body Preview</span>
      <pre class="body-text">{{ email.body_text.slice(0, 500) }}{{ email.body_text.length > 500 ? '...' : '' }}</pre>
    </div>
  </div>
</template>

<style scoped>
.email-preview {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.meta-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.meta-label {
  width: 80px;
  color: var(--text-muted);
  flex-shrink: 0;
  font-weight: 500;
}

.meta-value {
  color: var(--text-primary);
  word-break: break-all;
}

.meta-value.suspicious {
  color: #F97316;
}

.meta-value.subject {
  font-weight: 600;
}

.meta-value.mono {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.auth-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.auth-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-icon {
  font-size: 16px;
}

.body-preview {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.body-text {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  border-radius: 6px;
  padding: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
}
</style>
