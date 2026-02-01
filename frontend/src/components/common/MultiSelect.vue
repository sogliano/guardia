<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

interface Option {
  value: string
  label: string
}

const props = defineProps<{
  modelValue: string[]
  options: Option[]
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const selectedValues = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const displayText = computed(() => {
  const placeholder = props.placeholder || 'Select...'

  if (selectedValues.value.length === 0) {
    return placeholder
  }
  if (selectedValues.value.length === props.options.length) {
    return placeholder
  }
  if (selectedValues.value.length === 1) {
    const option = props.options.find(o => o.value === selectedValues.value[0])
    return `${placeholder}: ${option?.label || selectedValues.value[0]}`
  }
  return `${placeholder}: ${selectedValues.value.length} selected`
})

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function toggleOption(value: string) {
  const index = selectedValues.value.indexOf(value)
  if (index === -1) {
    selectedValues.value = [...selectedValues.value, value]
  } else {
    selectedValues.value = selectedValues.value.filter(v => v !== value)
  }
}

function isSelected(value: string): boolean {
  return selectedValues.value.includes(value)
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
  <div ref="dropdownRef" class="multi-select">
    <button type="button" class="select-trigger" @click="toggleDropdown">
      <span class="select-text">{{ displayText }}</span>
      <span class="material-symbols-rounded select-icon">
        {{ isOpen ? 'expand_less' : 'expand_more' }}
      </span>
    </button>
    <div v-if="isOpen" class="dropdown">
      <label
        v-for="option in options"
        :key="option.value"
        class="option"
        @click.stop
      >
        <input
          type="checkbox"
          :checked="isSelected(option.value)"
          @change="toggleOption(option.value)"
        />
        <span class="option-label">{{ option.label }}</span>
      </label>
    </div>
  </div>
</template>

<style scoped>
.multi-select {
  position: relative;
  min-width: 150px;
}

.select-trigger {
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

.select-trigger:hover {
  border-color: var(--text-muted);
}

.select-trigger:focus {
  outline: none;
  border-color: #00D4FF;
}

.select-text {
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-icon {
  font-size: 18px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-height: 280px;
  overflow-y: auto;
  z-index: 100;
}

.option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.option:hover {
  background: rgba(0, 212, 255, 0.08);
}

.option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #00D4FF;
  flex-shrink: 0;
}

.option-label {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
  flex: 1;
}

/* Scrollbar styling */
.dropdown::-webkit-scrollbar {
  width: 8px;
}

.dropdown::-webkit-scrollbar-track {
  background: var(--bg-inset);
  border-radius: 4px;
}

.dropdown::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.dropdown::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
