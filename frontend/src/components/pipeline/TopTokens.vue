<script setup lang="ts">
import { computed } from 'vue'
import type { XAIToken } from '@/types/case'

interface Props {
  tokens: XAIToken[]
  maxTokens?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxTokens: 5,
})

const displayTokens = computed(() => {
  const sorted = [...props.tokens].sort((a, b) => b.score - a.score)
  return sorted.slice(0, props.maxTokens)
})

const maxScore = computed(() => {
  if (displayTokens.value.length === 0) return 1
  return Math.max(...displayTokens.value.map(t => t.score))
})

function getBarWidth(score: number): string {
  const normalized = (score / maxScore.value) * 100
  return `${Math.max(normalized, 8)}%`
}

function getBarColor(score: number): string {
  const normalized = score / maxScore.value
  if (normalized > 0.7) return 'var(--color-critical)'
  if (normalized > 0.4) return 'var(--color-warn)'
  return 'var(--color-info)'
}
</script>

<template>
  <div class="top-tokens">
    <div class="tokens-header">
      <span class="material-symbols-rounded tokens-icon">psychology_alt</span>
      <span class="tokens-title">Key Influential Words</span>
      <span class="tokens-hint">(XAI)</span>
    </div>

    <div v-if="displayTokens.length === 0" class="tokens-empty">
      <span class="material-symbols-rounded">info</span>
      XAI data unavailable
    </div>

    <div v-else class="tokens-list">
      <div
        v-for="(token, index) in displayTokens"
        :key="index"
        class="token-row"
      >
        <span class="token-rank">{{ index + 1 }}</span>
        <span class="token-text">{{ token.token }}</span>
        <div class="token-bar-wrap">
          <div
            class="token-bar"
            :style="{
              width: getBarWidth(token.score),
              background: getBarColor(token.score),
            }"
          />
        </div>
        <span class="token-score">{{ (token.score * 100).toFixed(1) }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.top-tokens {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.tokens-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.tokens-icon {
  font-size: 18px;
  color: var(--color-info);
}

.tokens-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.tokens-hint {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
}

.tokens-empty {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 13px;
  padding: 8px 0;
}

.tokens-empty .material-symbols-rounded {
  font-size: 16px;
}

.tokens-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.token-row {
  display: grid;
  grid-template-columns: 20px 1fr 120px 50px;
  align-items: center;
  gap: 8px;
}

.token-rank {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-align: center;
}

.token-text {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  color: var(--text-primary);
  padding: 3px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.token-bar-wrap {
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.token-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.token-score {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  text-align: right;
}
</style>
