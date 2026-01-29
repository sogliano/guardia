<script setup lang="ts">
defineProps<{
  level: 'allow' | 'warn' | 'quarantine' | 'block'
}>()
</script>

<template>
  <span class="risk-badge" :class="level">
    {{ level.toUpperCase() }}
  </span>
</template>

<style scoped>
.risk-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.allow { background: rgba(74, 222, 128, 0.15); color: var(--color-allow); }
.warn { background: rgba(251, 191, 36, 0.15); color: var(--color-warn); }
.quarantine { background: rgba(249, 115, 22, 0.15); color: var(--color-quarantine); }
.block { background: rgba(239, 68, 68, 0.15); color: var(--color-block); }
</style>
