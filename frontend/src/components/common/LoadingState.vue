<script setup lang="ts">
defineProps<{
  message?: string
}>()
</script>

<template>
  <div class="loading-state">
    <span class="material-symbols-rounded spinning">progress_activity</span>
    <p>{{ message || 'Loading...' }}</p>
  </div>
</template>

<style scoped>
.loading-state {
  text-align: center;
  padding: 48px 24px;
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-state p {
  margin: 0;
}

.loading-state .spinning {
  font-size: 48px;
  color: var(--accent-cyan);
  opacity: 0.7;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinning {
  animation: spin 1s linear infinite;
}
</style>
