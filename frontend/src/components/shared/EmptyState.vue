<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  description?: string
}>()
</script>

<template>
  <div class="empty-state">
    <i v-if="icon" :class="icon" class="empty-icon"></i>
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  margin-bottom: var(--space-md);
}

.empty-state h3 {
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.empty-state p {
  color: var(--text-muted);
  font-size: 14px;
}
</style>
