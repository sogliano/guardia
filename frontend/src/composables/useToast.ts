import { ref } from 'vue'

export interface Toast {
  severity: 'success' | 'info' | 'warn' | 'error'
  summary: string
  detail?: string
  life?: number
}

const toasts = ref<Toast[]>([])

export function useToast() {
  function add(toast: Toast) {
    toasts.value.push(toast)
    if (toast.life) {
      setTimeout(() => {
        remove(toast)
      }, toast.life)
    }
  }

  function remove(toast: Toast) {
    const index = toasts.value.indexOf(toast)
    if (index > -1) toasts.value.splice(index, 1)
  }

  function success(summary: string, detail?: string) {
    add({ severity: 'success', summary, detail, life: 3000 })
  }

  function error(summary: string, detail?: string) {
    add({ severity: 'error', summary, detail, life: 5000 })
  }

  return { toasts, add, remove, success, error }
}
