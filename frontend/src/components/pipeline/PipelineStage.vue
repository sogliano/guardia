<script setup lang="ts">
defineProps<{ stage: string; score: number | null; active?: boolean }>()
</script>

<template>
  <div class="pipeline-stage" :class="{ active }">
    <span class="stage-label">{{ stage }}</span>
    <span v-if="score !== null" class="stage-score">{{ (score * 100).toFixed(0) }}%</span>
  </div>
</template>

<style scoped>
.pipeline-stage {
  padding: var(--space-md);
  background: var(--bg-tertiary);
  border-radius: var(--border-radius);
  text-align: center;
}
.pipeline-stage.active { border: 1px solid var(--accent-cyan); }
.stage-label { display: block; color: var(--text-secondary); font-size: 12px; text-transform: uppercase; }
.stage-score { display: block; color: var(--text-primary); font-size: 20px; font-weight: 700; margin-top: 4px; }
</style>
