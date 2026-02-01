<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  modelValue: { from: string | null; to: string | null }
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: { from: string | null; to: string | null }): void
}>()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const dateFrom = ref(props.modelValue.from || '')
const dateTo = ref(props.modelValue.to || '')

const displayText = computed(() => {
  if (!dateFrom.value && !dateTo.value) {
    return 'Date Range'
  }
  if (dateFrom.value && dateTo.value) {
    return `${formatDisplayDate(dateFrom.value)} - ${formatDisplayDate(dateTo.value)}`
  }
  if (dateFrom.value) {
    return `From ${formatDisplayDate(dateFrom.value)}`
  }
  return `Until ${formatDisplayDate(dateTo.value)}`
})

function formatDisplayDate(date: string): string {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function applyDates() {
  emit('update:modelValue', {
    from: dateFrom.value || null,
    to: dateTo.value || null,
  })
  isOpen.value = false
}

function clearDates() {
  dateFrom.value = ''
  dateTo.value = ''
  emit('update:modelValue', { from: null, to: null })
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="dropdownRef" class="date-range-picker">
    <button type="button" class="picker-trigger" @click="toggleDropdown">
      <span class="picker-text">{{ displayText }}</span>
      <span class="material-symbols-rounded picker-icon">
        {{ isOpen ? 'expand_less' : 'expand_more' }}
      </span>
    </button>
    <div v-if="isOpen" class="dropdown">
      <div class="date-inputs">
        <div class="input-group">
          <label>From</label>
          <input
            v-model="dateFrom"
            type="date"
            class="date-input"
            @click.stop
          />
        </div>
        <div class="input-group">
          <label>To</label>
          <input
            v-model="dateTo"
            type="date"
            class="date-input"
            @click.stop
          />
        </div>
      </div>
      <div class="actions">
        <button type="button" class="btn-clear" @click.stop="clearDates">Clear</button>
        <button type="button" class="btn-apply" @click.stop="applyDates">Apply</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.date-range-picker {
  position: relative;
  min-width: 220px;
}

.picker-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  background: var(--bg-inset);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.picker-trigger:hover {
  border-color: var(--text-muted);
}

.picker-trigger:focus {
  outline: none;
  border-color: #00D4FF;
}

.picker-text {
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.picker-icon {
  font-size: 18px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
  padding: 16px;
  min-width: 280px;
}

.date-inputs {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.date-input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  background: var(--bg-inset);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.date-input:focus {
  border-color: #00D4FF;
}

.date-input::-webkit-calendar-picker-indicator {
  cursor: pointer;
  filter: invert(0.6);
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.btn-clear,
.btn-apply {
  padding: 6px 16px;
  border: none;
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-clear {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-color);
}

.btn-clear:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.btn-apply {
  background: #00D4FF;
  color: #060B14;
}

.btn-apply:hover {
  opacity: 0.9;
}
</style>
