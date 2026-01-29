import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Setting } from '@/types/setting'
import { fetchSettings as fetchSettingsApi, updateSetting } from '@/services/settingsService'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Setting[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const thresholds = ref({
    allow: 0.3,
    warn: 0.6,
    quarantine: 0.8,
  })

  const warnThreshold = computed(() => thresholds.value.warn)
  const quarantineThreshold = computed(() => thresholds.value.quarantine)

  async function fetchSettings() {
    loading.value = true
    error.value = null
    try {
      settings.value = await fetchSettingsApi()
      const t = settings.value.find((s) => s.key === 'thresholds')
      if (t && typeof t.value === 'object' && t.value !== null) {
        const val = t.value as Record<string, number>
        thresholds.value = {
          allow: val.allow ?? 0.3,
          warn: val.warn ?? 0.6,
          quarantine: val.quarantine ?? 0.8,
        }
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load settings'
    } finally {
      loading.value = false
    }
  }

  async function saveThresholds(warn: number, quarantine: number) {
    thresholds.value.warn = warn
    thresholds.value.quarantine = quarantine
    await updateSetting('thresholds', { value: thresholds.value })
    await fetchSettings()
  }

  return {
    settings, thresholds, warnThreshold, quarantineThreshold,
    loading, error, fetchSettings, saveThresholds,
  }
})
