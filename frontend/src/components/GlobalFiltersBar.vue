<script setup lang="ts">
import { ref, watch } from 'vue'
import { useGlobalFiltersStore } from '@/stores/globalFilters'

const globalFilters = useGlobalFiltersStore()

const selected = ref('all')
const showDateInputs = ref(false)
const dateFrom = ref('')
const dateTo = ref('')

function onChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  selected.value = val
  if (val === 'custom') {
    showDateInputs.value = true
    return
  }
  showDateInputs.value = false
  dateFrom.value = ''
  dateTo.value = ''
  if (val === 'all') {
    globalFilters.clearFilters()
  } else {
    globalFilters.setDatePreset(val)
  }
}

function onDateChange() {
  if (dateFrom.value && dateTo.value) {
    globalFilters.setDateRange([new Date(dateFrom.value), new Date(dateTo.value)])
  } else if (dateFrom.value) {
    globalFilters.setDateRange([new Date(dateFrom.value), new Date()])
  }
}

// Sync date inputs when store changes externally (e.g. TopSenders click)
watch(() => globalFilters.dateRange, (val) => {
  if (!val || val.length === 0) {
    if (selected.value !== 'custom') {
      dateFrom.value = ''
      dateTo.value = ''
    }
  }
})
</script>

<template>
  <div class="gf">
    <span class="material-symbols-rounded gf-icon">filter_list</span>
    <select class="gf-select" :value="selected" @change="onChange">
      <option value="all">All time</option>
      <option value="30d">Last 30 days</option>
      <option value="7d">Last 7 days</option>
      <option value="24h">Last 24 hours</option>
      <option value="custom">Custom range</option>
    </select>

    <template v-if="showDateInputs">
      <input
        type="date"
        class="gf-date"
        v-model="dateFrom"
        @change="onDateChange"
      />
      <span class="gf-dash">—</span>
      <input
        type="date"
        class="gf-date"
        v-model="dateTo"
        @change="onDateChange"
      />
    </template>
  </div>
</template>

<style scoped>
.gf {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin: -12px 0;
}

.gf-icon {
  font-size: 20px;
  color: var(--text-dim);
}

.gf-select {
  height: 30px;
  padding: 0 26px 0 8px;
  font-size: 12px;
  font-family: var(--font-family);
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath fill='%236B7280' d='M2 3.5L5 7l3-3.5H2z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  transition: border-color 0.12s;
}

.gf-select:hover {
  border-color: var(--text-dim);
}

.gf-select:focus {
  border-color: var(--accent-cyan);
}

.gf-select option {
  background: var(--bg-card);
  color: var(--text-primary);
}

.gf-date {
  height: 28px;
  padding: 0 6px;
  font-size: 12px;
  font-family: var(--font-family);
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  outline: none;
  transition: border-color 0.12s;
  color-scheme: dark;
}

.gf-date:focus {
  border-color: var(--accent-cyan);
}

.gf-dash {
  font-size: 11px;
  color: var(--text-dim);
}
</style>
