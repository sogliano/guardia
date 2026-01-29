<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUser } from '@clerk/vue'
import { useRoute } from 'vue-router'

const authStore = useAuthStore()
const { user: clerkUser } = useUser()
const route = useRoute()

const breadcrumbs = computed(() => {
  const crumbs: { label: string; path?: string }[] = []
  const name = route.name as string
  if (!name || name === 'dashboard') {
    crumbs.push({ label: 'Dashboard' })
  } else {
    crumbs.push({ label: 'Dashboard', path: '/' })
    const pageNames: Record<string, string> = {
      cases: 'Cases',
      'case-detail': 'Case Detail',
      quarantine: 'Quarantine',
      emails: 'Email Explorer',
      policies: 'Policies',
      alerts: 'Alerts',
      reports: 'Reports',
      settings: 'Settings',
      'fp-review': 'FP Review',
      notifications: 'Notifications',
    }
    crumbs.push({ label: pageNames[name] ?? name })
  }
  return crumbs
})
</script>

<template>
  <header class="topbar">
    <div class="topbar-left">
      <template v-for="(crumb, i) in breadcrumbs" :key="i">
        <RouterLink v-if="crumb.path" :to="crumb.path" class="breadcrumb-link">{{ crumb.label }}</RouterLink>
        <span v-else class="breadcrumb-current">{{ crumb.label }}</span>
        <span v-if="i < breadcrumbs.length - 1" class="breadcrumb-sep">/</span>
      </template>
    </div>

    <div class="topbar-center">
      <div class="search-box">
        <span class="material-symbols-rounded search-icon">search</span>
        <span class="search-placeholder">Search cases, emails, domains...</span>
      </div>
    </div>

    <div class="topbar-right">
      <RouterLink to="/notifications" class="icon-btn">
        <span class="material-symbols-rounded">notifications</span>
      </RouterLink>
      <RouterLink to="/settings" class="user-chip">
        <img
          v-if="clerkUser?.imageUrl"
          :src="clerkUser.imageUrl"
          :alt="authStore.user?.full_name ?? 'User'"
          class="user-avatar-img"
        />
        <div v-else class="user-avatar">
          {{ (authStore.user?.full_name ?? 'U')[0] }}
        </div>
        <span class="user-chip-name">{{ authStore.user?.full_name ?? 'User' }}</span>
      </RouterLink>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--topbar-height);
  padding: 0 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.breadcrumb-link {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  text-decoration: none;
  letter-spacing: 0.3px;
  transition: color 0.15s;
}

.breadcrumb-link:hover {
  color: var(--accent-cyan);
}

.breadcrumb-sep {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-dim);
}

.breadcrumb-current {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.topbar-center {
  flex: 0 1 400px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  padding: 0 14px;
  background: var(--bg-inset);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: border-color 0.2s;
}

.search-box:hover {
  border-color: rgba(0, 212, 255, 0.25);
}

.search-icon {
  font-size: 15px;
  color: var(--text-muted);
}

.search-placeholder {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.2px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  color: var(--text-muted);
  text-decoration: none;
  border-radius: var(--border-radius);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.icon-btn:hover {
  color: var(--accent-cyan);
  border-color: rgba(0, 212, 255, 0.15);
  background: rgba(0, 212, 255, 0.04);
}

.icon-btn .material-symbols-rounded {
  font-size: 19px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s;
}

.user-chip:hover {
  border-color: rgba(0, 212, 255, 0.2);
  background: rgba(0, 212, 255, 0.04);
}

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 13px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
}

.user-avatar-img {
  width: 26px;
  height: 26px;
  border-radius: 13px;
  object-fit: cover;
  border: 1px solid rgba(0, 212, 255, 0.25);
}

.user-chip-name {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.3px;
}
</style>
