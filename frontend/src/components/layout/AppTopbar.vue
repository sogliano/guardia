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
  font-size: 13px;
  font-weight: normal;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.15s;
}

.breadcrumb-link:hover {
  color: var(--text-primary);
}

.breadcrumb-sep {
  font-size: 13px;
  color: var(--text-dim);
}

.breadcrumb-current {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.topbar-center {
  flex: 0 1 400px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
}

.search-icon {
  font-size: 16px;
  color: var(--text-muted);
}

.search-placeholder {
  font-size: 13px;
  color: var(--text-muted);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--border-radius-sm);
  transition: color 0.15s;
}

.icon-btn:hover {
  color: var(--text-primary);
}

.icon-btn .material-symbols-rounded {
  font-size: 20px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: var(--border-radius-sm);
  text-decoration: none;
  color: var(--text-primary);
  transition: background 0.15s;
}

.user-chip:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 14px;
  background: var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan);
  font-size: 12px;
  font-weight: 600;
}

.user-avatar-img {
  width: 28px;
  height: 28px;
  border-radius: 14px;
  object-fit: cover;
}

.user-chip-name {
  font-size: 13px;
  font-weight: 500;
}
</style>
