<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import type { Case } from '@/types/case'

defineProps<{
  cases: Case[]
  totalRecords: number
  loading: boolean
  rows: number
  first: number
}>()

const emit = defineEmits<{
  page: [event: { page: number; rows: number; first: number }]
  release: [caseId: string]
  keep: [caseId: string]
  delete: [caseId: string]
}>()

function formatScore(score: number | null): string {
  if (score === null) return '—'
  return (score * 100).toFixed(0)
}

function scoreColor(score: number | null): string {
  if (score === null) return '#6B7280'
  if (score >= 0.8) return '#EF4444'
  if (score >= 0.6) return '#F97316'
  if (score >= 0.3) return '#F59E0B'
  return '#22C55E'
}
</script>

<template>
  <DataTable
    :value="cases"
    :total-records="totalRecords"
    :loading="loading"
    :rows="rows"
    :first="first"
    lazy
    paginator
    :rows-per-page-options="[10, 20, 50]"
    striped-rows
    row-hover
    @page="emit('page', $event)"
  >
    <Column field="created_at" header="Date" style="width: 120px">
      <template #body="{ data }">
        <span class="text-sm text-muted">
          {{ formatDistanceToNow(new Date(data.created_at), { addSuffix: true }) }}
        </span>
      </template>
    </Column>
    <Column field="status" header="Status" style="width: 100px">
      <template #body="{ data }">
        <Tag :value="data.status" severity="warn" />
      </template>
    </Column>
    <Column field="risk_level" header="Risk" style="width: 90px">
      <template #body="{ data }">
        <Tag v-if="data.risk_level" :value="data.risk_level" severity="warn" />
        <span v-else class="text-muted">—</span>
      </template>
    </Column>
    <Column field="final_score" header="Score" style="width: 80px">
      <template #body="{ data }">
        <span class="score-value" :style="{ color: scoreColor(data.final_score) }">
          {{ formatScore(data.final_score) }}
        </span>
      </template>
    </Column>
    <Column field="threat_category" header="Threat" style="min-width: 120px">
      <template #body="{ data }">
        <span v-if="data.threat_category" class="text-sm">{{ data.threat_category.replace('_', ' ') }}</span>
        <span v-else class="text-muted">—</span>
      </template>
    </Column>
    <Column header="Actions" style="width: 200px">
      <template #body="{ data }">
        <div class="actions">
          <Button label="Release" severity="success" size="small" text @click="emit('release', data.id)" />
          <Button label="Keep" severity="warn" size="small" text @click="emit('keep', data.id)" />
          <Button label="Delete" severity="danger" size="small" text @click="emit('delete', data.id)" />
        </div>
      </template>
    </Column>
  </DataTable>
</template>

<style scoped>
.text-sm {
  font-size: 13px;
}
.text-muted {
  color: var(--text-muted);
  font-size: 13px;
}
.score-value {
  font-weight: 600;
  font-size: 13px;
}
.actions {
  display: flex;
  gap: 4px;
}
</style>
