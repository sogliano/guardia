<script setup lang="ts">
import { ref } from 'vue'
import FormInput from '@/components/common/FormInput.vue'
import { ingestEmail } from '@/services/emailService'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'ingested'): void
}>()

const ingesting = ref(false)
const ingestError = ref('')
const validationErrors = ref<Record<string, string>>({})

const ingestForm = ref({
  message_id: `test-${Date.now()}@guardia.local`,
  sender_email: '',
  sender_name: '',
  recipient_email: 'security@strikesecurity.io',
  subject: '',
  body_text: '',
})

function resetForm() {
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

function validateForm(): boolean {
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
  if (!validateForm()) return

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
    emit('ingested')
    emit('close')
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } } }
    ingestError.value = error.response?.data?.detail || 'Failed to ingest email'
  } finally {
    ingesting.value = false
  }
}

function handleClose() {
  emit('close')
}

defineExpose({ resetForm })
</script>

<template>
  <div class="modal-overlay" @click="handleClose">
    <div class="modal-card" @click.stop>
      <div class="modal-header">
        <h2>Ingest Email</h2>
        <button class="close-btn" @click="handleClose">
          <span class="material-symbols-rounded">close</span>
        </button>
      </div>
      <form @submit.prevent="submitIngest" class="modal-body">
        <FormInput
          v-model="ingestForm.message_id"
          label="Message ID"
          type="text"
          required
          :error="validationErrors.message_id"
        />
        <FormInput
          v-model="ingestForm.sender_email"
          label="Sender Email"
          type="email"
          required
          placeholder="attacker@example.com"
          :error="validationErrors.sender_email"
        />
        <FormInput
          v-model="ingestForm.sender_name"
          label="Sender Name"
          type="text"
          placeholder="John Doe"
        />
        <FormInput
          v-model="ingestForm.recipient_email"
          label="Recipient Email"
          type="email"
          required
          :error="validationErrors.recipient_email"
        />
        <FormInput
          v-model="ingestForm.subject"
          label="Subject"
          type="text"
          placeholder="Urgent: Password Reset Required"
        />
        <div class="form-group">
          <label>Body Text</label>
          <textarea v-model="ingestForm.body_text" class="form-textarea" rows="6" placeholder="Email body content..."></textarea>
        </div>
        <div v-if="ingestError" class="error-message">{{ ingestError }}</div>
        <div class="modal-footer">
          <button type="button" class="btn-outline" @click="handleClose" :disabled="ingesting">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="ingesting">
            <span v-if="ingesting" class="material-symbols-rounded btn-icon spinning">progress_activity</span>
            <span v-else class="material-symbols-rounded btn-icon">upload</span>
            {{ ingesting ? 'Ingesting...' : 'Ingest Email' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
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
  resize: vertical;
  min-height: 120px;
}

.form-textarea:focus {
  border-color: #00D4FF;
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

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
