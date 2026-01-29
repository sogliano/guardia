<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
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
  rowClick: [caseItem: Case]
}>()

function riskSeverity(risk: string | null): 'danger' | 'warn' | 'info' | 'success' | undefined {
  if (!risk) return undefined
  const map: Record<string, 'danger' | 'warn' | 'info' | 'success'> = {
    critical: 'danger',
    high: 'warn',
    medium: 'info',
    low: 'success',
  }
  return map[risk]
}

function verdictSeverity(verdict: string | null): 'danger' | 'warn' | 'info' | 'success' | undefined {
  if (!verdict) return undefined
  const map: Record<string, 'danger' | 'warn' | 'info' | 'success'> = {
    blocked: 'danger',
    quarantined: 'warn',
    warned: 'info',
    allowed: 'success',
  }
  return map[verdict]
}

function formatScore(score: number | null): string {
  if (score === null) return '—'
  return (score * 100).toFixed(0)
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
    class="case-table"
    @page="emit('page', $event)"
    @row-click="emit('rowClick', $event.data)"
  >
    <Column field="created_at" header="Date" sortable style="width: 120px">
      <template #body="{ data }">
        <span class="text-sm text-muted">
          {{ formatDistanceToNow(new Date(data.created_at), { addSuffix: true }) }}
        </span>
      </template>
    </Column>
    <Column field="status" header="Status" style="width: 100px">
      <template #body="{ data }">
        <Tag :value="data.status" severity="info" />
      </template>
    </Column>
    <Column field="risk_level" header="Risk" style="width: 90px">
      <template #body="{ data }">
        <Tag v-if="data.risk_level" :value="data.risk_level" :severity="riskSeverity(data.risk_level)" />
        <span v-else class="text-muted">—</span>
      </template>
    </Column>
    <Column field="final_score" header="Score" sortable style="width: 70px">
      <template #body="{ data }">
        <span class="score-value">{{ formatScore(data.final_score) }}</span>
      </template>
    </Column>
    <Column field="verdict" header="Verdict" style="width: 100px">
      <template #body="{ data }">
        <Tag v-if="data.verdict" :value="data.verdict" :severity="verdictSeverity(data.verdict)" />
        <span v-else class="text-muted">—</span>
      </template>
    </Column>
    <Column field="threat_category" header="Threat" style="min-width: 140px">
      <template #body="{ data }">
        <span v-if="data.threat_category" class="text-sm">{{ data.threat_category.replace('_', ' ') }}</span>
        <span v-else class="text-muted">—</span>
      </template>
    </Column>
  </DataTable>
</template>

<style scoped>
.case-table {
  cursor: pointer;
}
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
</style>
