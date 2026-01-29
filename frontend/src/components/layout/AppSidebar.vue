<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCasesStore } from '@/stores/cases'
import { useQuarantineStore } from '@/stores/quarantine'
import { UserButton } from '@clerk/vue'
import type { UserRole } from '@/types/auth'

const route = useRoute()
const authStore = useAuthStore()
const casesStore = useCasesStore()
const quarantineStore = useQuarantineStore()

interface MenuItem {
  label: string
  icon: string
  to: string
  roles?: UserRole[]
  badgeKey?: string
}

const allMenuItems: MenuItem[] = [
  { label: 'Dashboard', icon: 'dashboard', to: '/' },
  { label: 'Cases', icon: 'folder', to: '/cases', badgeKey: 'cases' },
  { label: 'Quarantine', icon: 'shield', to: '/quarantine', badgeKey: 'quarantine' },
  { label: 'Emails', icon: 'mail', to: '/emails' },
  { label: 'Policies', icon: 'tune', to: '/policies', roles: ['administrator', 'analyst'] },
  { label: 'Alerts', icon: 'notifications', to: '/alerts', roles: ['administrator', 'analyst'] },
  { label: 'FP Review', icon: 'rate_review', to: '/fp-review', roles: ['administrator', 'analyst'] },
  { label: 'Reports', icon: 'bar_chart', to: '/reports' },
  { label: 'Settings', icon: 'settings', to: '/settings', roles: ['administrator'] },
]

const menuItems = computed(() => {
  const role = authStore.user?.role
  if (!role) return allMenuItems
  return allMenuItems.filter(item => !item.roles || item.roles.includes(role))
})

function getBadge(key: string | undefined): number | null {
  if (!key) return null
  if (key === 'cases' && casesStore.total > 0) return casesStore.total
  if (key === 'quarantine' && quarantineStore.total > 0) return quarantineStore.total
  return null
}

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="material-symbols-rounded sidebar-logo-icon">shield</span>
      <span class="sidebar-logo-text">Guard-IA</span>
    </div>

    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.to) }"
      >
        <span class="material-symbols-rounded nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
        <span v-if="getBadge(item.badgeKey)" class="nav-badge">{{ getBadge(item.badgeKey) }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <UserButton />
      <div class="user-info">
        <span class="user-name">{{ authStore.user?.full_name ?? 'User' }}</span>
        <span class="user-role">{{ authStore.user?.role ?? 'Analyst' }}</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--topbar-height);
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-logo-icon {
  font-size: 26px;
  color: var(--accent-cyan);
  filter: drop-shadow(0 0 6px rgba(0, 212, 255, 0.4));
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { filter: drop-shadow(0 0 6px rgba(0, 212, 255, 0.4)); }
  50% { filter: drop-shadow(0 0 12px rgba(0, 212, 255, 0.7)); }
}

.sidebar-logo-text {
  font-family: var(--font-mono);
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 40px;
  padding: 0 12px;
  border-radius: var(--border-radius-sm);
  color: var(--text-muted);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.3px;
  transition: all 0.2s;
}

.nav-item:hover {
  color: var(--text-primary);
  background: rgba(0, 212, 255, 0.04);
}

.nav-item.active {
  color: var(--accent-cyan);
  background: rgba(0, 212, 255, 0.08);
  box-shadow: inset 3px 0 0 var(--accent-cyan);
}

.nav-icon {
  font-size: 19px;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  opacity: 0.7;
}

.nav-item:hover .nav-icon,
.nav-item.active .nav-icon {
  opacity: 1;
}

.nav-item.active .nav-icon {
  filter: drop-shadow(0 0 4px rgba(0, 212, 255, 0.5));
}

.nav-label {
  flex: 1;
}

.nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(0, 212, 255, 0.12);
  color: #00D4FF;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.15);
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.user-name {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.3px;
}

.user-role {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  opacity: 0.7;
}
</style>
