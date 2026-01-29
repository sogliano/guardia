<script setup lang="ts">
import type { TopSenderItem } from '@/types/dashboard'
import { useGlobalFiltersStore } from '@/stores/globalFilters'
import { scoreColor } from '@/utils/colors'

defineProps<{
  senders: TopSenderItem[]
}>()

const globalFilters = useGlobalFiltersStore()

function filterBySender(sender: string) {
  globalFilters.setSender(sender)
}

</script>

<template>
  <div class="card top-senders">
    <div class="card-header">
      <h3>Top Senders</h3>
    </div>
    <div v-if="senders.length === 0" class="empty">No sender data available</div>
    <div v-else class="sender-list">
      <div
        v-for="s in senders"
        :key="s.sender"
        class="sender-row"
        @click="filterBySender(s.sender)"
      >
        <div class="sender-info">
          <span class="sender-email">{{ s.sender }}</span>
          <span class="sender-count">{{ s.count }} email{{ s.count !== 1 ? 's' : '' }}</span>
        </div>
        <div class="sender-score" :style="{ color: scoreColor(s.avg_score) }">
          {{ (s.avg_score * 100).toFixed(0) }}%
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.top-senders {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 20px;
}

.card-header {
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.empty {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  padding: 24px 0;
}

.sender-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sender-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}

.sender-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.sender-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.sender-email {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sender-count {
  font-size: 12px;
  color: var(--text-muted);
}

.sender-score {
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  margin-left: 12px;
}
</style>
