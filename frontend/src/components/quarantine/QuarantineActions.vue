<script setup lang="ts">
const emit = defineEmits<{ approve: []; reject: [] }>()
</script>

<template>
  <div class="quarantine-actions">
    <button class="btn-approve" @click="emit('approve')">Approve</button>
    <button class="btn-reject" @click="emit('reject')">Reject</button>
  </div>
</template>

<style scoped>
.quarantine-actions { display: flex; gap: var(--space-sm); }
.btn-approve, .btn-reject { padding: 6px 16px; border: none; border-radius: var(--border-radius); cursor: pointer; font-weight: 600; }
.btn-approve { background: var(--color-allow); color: var(--bg-primary); }
.btn-reject { background: var(--color-block); color: white; }
</style>
