<script setup lang="ts">
import { watch } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useAuth as useClerkAuth } from '@clerk/vue'
import { useAuthStore } from '@/stores/auth'
import { setClerkGetToken } from '@/services/api'

const { isLoaded, isSignedIn, getToken } = useClerkAuth()
const authStore = useAuthStore()
const router = useRouter()

// Bridge Clerk's getToken to our axios interceptor
setClerkGetToken(async () => {
  if (!getToken.value) {
    console.warn('Clerk not initialized - getToken.value is null')
    return null
  }

  try {
    const token = await getToken.value({ template: 'guardia-backend' })

    if (!token) {
      console.error('Failed to get authentication token from Clerk')
    }

    return token
  } catch (error) {
    console.error('Error getting token from Clerk:', error)
    return null
  }
})

// Guard all navigation: wait for Clerk to load, then enforce auth
router.beforeEach(async (to) => {
  // Wait for Clerk to finish loading
  if (!isLoaded.value) {
    await new Promise<void>((resolve) => {
      const stop = watch(isLoaded, (loaded) => {
        if (loaded) { stop(); resolve() }
      }, { immediate: true })
    })
  }

  if (isSignedIn.value && to.name === 'login') {
    return { name: 'dashboard' }
  }
  if (!isSignedIn.value && to.name !== 'login') {
    return { name: 'login' }
  }
})

// Sync Clerk auth state → our store + handle live sign-in/sign-out
watch(
  [isLoaded, isSignedIn],
  async ([loaded, signedIn]) => {
    if (!loaded) return

    if (signedIn) {
      await authStore.fetchProfile()
      if (router.currentRoute.value.name === 'login') {
        router.push({ name: 'dashboard' })
      }
    } else {
      authStore.clearProfile()
      if (router.currentRoute.value.name !== 'login') {
        router.push({ name: 'login' })
      }
    }
  },
  { immediate: true },
)
</script>

<template>
  <RouterView v-if="isLoaded" />
</template>
