<script setup lang="ts">
defineProps<{
  status: 'pending' | 'analyzing' | 'analyzed' | 'resolved'
}>()

const statusColors: Record<string, string> = {
  pending: '#8899B4',
  analyzing: '#FBBF24',
  analyzed: '#00D4FF',
  resolved: '#4ADE80',
}
</script>

<template>
  <span class="status-tag" :style="{ color: statusColors[status], borderColor: statusColors[status] }">
    {{ status }}
  </span>
</template>

<style scoped>
.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 12px;
  text-transform: capitalize;
}
</style>
