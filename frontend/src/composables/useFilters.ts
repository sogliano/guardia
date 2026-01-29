import { ref, watch } from 'vue'

export function useFilters<T extends Record<string, unknown>>(defaults: T) {
  const filters = ref<T>({ ...defaults }) as { value: T }

  function reset() {
    filters.value = { ...defaults }
  }

  function set(key: keyof T, value: T[keyof T]) {
    filters.value = { ...filters.value, [key]: value }
  }

  return { filters, reset, set }
}
