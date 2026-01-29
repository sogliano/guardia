<script setup lang="ts">
import { ref } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'

const emit = defineEmits<{
  filter: [filters: { status?: string; risk?: string }]
}>()

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Analyzing', value: 'analyzing' },
  { label: 'Analyzed', value: 'analyzed' },
  { label: 'Quarantined', value: 'quarantined' },
  { label: 'Resolved', value: 'resolved' },
]

const riskOptions = [
  { label: 'All Risk Levels', value: '' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

const selectedStatus = ref('')
const selectedRisk = ref('')

function applyFilters() {
  emit('filter', {
    status: selectedStatus.value || undefined,
    risk: selectedRisk.value || undefined,
  })
}

function clearFilters() {
  selectedStatus.value = ''
  selectedRisk.value = ''
  emit('filter', {})
}
</script>

<template>
  <div class="case-filters">
    <Select
      v-model="selectedStatus"
      :options="statusOptions"
      option-label="label"
      option-value="value"
      placeholder="Status"
      class="filter-select"
      @change="applyFilters"
    />
    <Select
      v-model="selectedRisk"
      :options="riskOptions"
      option-label="label"
      option-value="value"
      placeholder="Risk Level"
      class="filter-select"
      @change="applyFilters"
    />
    <Button label="Clear" severity="secondary" text size="small" @click="clearFilters" />
  </div>
</template>

<style scoped>
.case-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.filter-select {
  width: 180px;
}
</style>
