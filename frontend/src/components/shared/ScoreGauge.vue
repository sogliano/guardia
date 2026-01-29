<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number
}>()

const color = computed(() => {
  if (props.score < 0.3) return 'var(--color-allow)'
  if (props.score < 0.6) return 'var(--color-warn)'
  if (props.score < 0.8) return 'var(--color-quarantine)'
  return 'var(--color-block)'
})

const percentage = computed(() => Math.round(props.score * 100))
</script>

<template>
  <div class="score-gauge">
    <div class="gauge-bar">
      <div class="gauge-fill" :style="{ width: percentage + '%', background: color }"></div>
    </div>
    <span class="gauge-value" :style="{ color }">{{ percentage }}%</span>
  </div>
</template>

<style scoped>
.score-gauge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gauge-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.gauge-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.gauge-value {
  font-size: 13px;
  font-weight: 600;
  min-width: 40px;
  text-align: right;
}
</style>
