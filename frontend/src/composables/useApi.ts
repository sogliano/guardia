import { ref } from 'vue'

export function useApi<T>(apiFn: (...args: unknown[]) => Promise<T>) {
  const data = ref<T | null>(null) as { value: T | null }
  const error = ref<string | null>(null)
  const loading = ref(false)

  async function execute(...args: unknown[]) {
    loading.value = true
    error.value = null
    try {
      data.value = await apiFn(...args)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  return { data, error, loading, execute }
}
