import { ref, computed } from 'vue'

export function usePagination(initialSize = 20) {
  const page = ref(1)
  const size = ref(initialSize)
  const total = ref(0)

  const totalPages = computed(() => Math.ceil(total.value / size.value))
  const hasNext = computed(() => page.value < totalPages.value)
  const hasPrev = computed(() => page.value > 1)

  function nextPage() {
    if (hasNext.value) page.value++
  }

  function prevPage() {
    if (hasPrev.value) page.value--
  }

  function setPage(p: number) {
    page.value = Math.max(1, Math.min(p, totalPages.value))
  }

  return { page, size, total, totalPages, hasNext, hasPrev, nextPage, prevPage, setPage }
}
