<script setup lang="ts">
defineProps<{ explanation?: string }>()
</script>

<template>
  <div class="llm-explanation">
    <h4>LLM Explanation</h4>
    <p v-if="explanation">{{ explanation }}</p>
    <p v-else class="placeholder">No explanation available</p>
  </div>
</template>

<style scoped>
.llm-explanation { background: var(--bg-tertiary); border-radius: var(--border-radius); padding: var(--space-md); }
.llm-explanation h4 { color: var(--accent-cyan); margin-bottom: var(--space-sm); }
.placeholder { color: var(--text-muted); }
</style>
