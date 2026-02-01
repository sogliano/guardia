<template>
  <div class="error-state">
    <span class="material-symbols-rounded">error</span>
    <p>{{ message }}</p>
    <button v-if="onRetry" @click="onRetry" class="retry-btn">Retry</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: string
  onRetry?: () => void
}>()
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: #6B7280;
}

.error-state .material-symbols-rounded {
  font-size: 4rem;
  color: #EF4444;
  margin-bottom: 1rem;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  background: #3B82F6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
}

.retry-btn:hover {
  background: #2563EB;
}
</style>
