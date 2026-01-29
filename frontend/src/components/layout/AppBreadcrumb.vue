<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

const breadcrumbs = computed(() => {
  const parts = route.path.split('/').filter(Boolean)
  return parts.map((part, index) => ({
    label: part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' '),
    path: '/' + parts.slice(0, index + 1).join('/'),
  }))
})
</script>

<template>
  <nav class="breadcrumb">
    <RouterLink to="/" class="breadcrumb-item">Home</RouterLink>
    <template v-for="crumb in breadcrumbs" :key="crumb.path">
      <span class="separator">/</span>
      <RouterLink :to="crumb.path" class="breadcrumb-item">{{ crumb.label }}</RouterLink>
    </template>
  </nav>
</template>

<style scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 13px;
}

.breadcrumb-item {
  color: var(--text-secondary);
  text-decoration: none;
}

.breadcrumb-item:hover {
  color: var(--accent-cyan);
}

.separator {
  color: var(--text-muted);
}
</style>
