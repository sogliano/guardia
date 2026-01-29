<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click="emit('cancel')">
      <div class="dialog" @click.stop>
        <h3>{{ title }}</h3>
        <p>{{ message }}</p>
        <div class="dialog-actions">
          <button class="btn-cancel" @click="emit('cancel')">{{ cancelLabel ?? 'Cancel' }}</button>
          <button class="btn-confirm" @click="emit('confirm')">{{ confirmLabel ?? 'Confirm' }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--border-radius);
  padding: var(--space-lg);
  min-width: 360px;
}

.dialog h3 {
  margin-bottom: var(--space-sm);
}

.dialog p {
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
}

.dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
}

.btn-cancel, .btn-confirm {
  padding: 8px 16px;
  border-radius: var(--border-radius);
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.btn-confirm {
  background: var(--accent-cyan);
  color: var(--bg-primary);
  font-weight: 600;
}
</style>
