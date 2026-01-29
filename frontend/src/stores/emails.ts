import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Email } from '@/types/email'
import { fetchEmails as fetchEmailsApi } from '@/services/emailService'
import { useGlobalFiltersStore } from '@/stores/globalFilters'

export const useEmailsStore = defineStore('emails', () => {
  const emails = ref<Email[]>([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(25)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const globalFilters = useGlobalFiltersStore()
  const filters = ref<{
    search?: string
    risk_level?: string
    sender?: string
    date_from?: string
    date_to?: string
  }>({})

  async function fetchEmails() {
    loading.value = true
    error.value = null
    try {
      const gf = globalFilters.filterParams
      const result = await fetchEmailsApi({
        page: page.value,
        size: size.value,
        ...filters.value,
        ...gf,
      })
      emails.value = result.items
      total.value = result.total
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load emails'
    } finally {
      loading.value = false
    }
  }

  function setPage(p: number) {
    page.value = p
    fetchEmails()
  }

  function setFilters(f: typeof filters.value) {
    filters.value = f
    page.value = 1
    fetchEmails()
  }

  watch(() => globalFilters.filterParams, () => {
    page.value = 1
    fetchEmails()
  }, { deep: true })

  return { emails, total, page, size, loading, error, filters, fetchEmails, setPage, setFilters }
})
