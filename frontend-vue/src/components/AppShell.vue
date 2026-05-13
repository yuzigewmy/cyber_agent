<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">A</div>
        <div>
          <strong>Cyber Agent</strong>
          <span>Attack-Defense Console</span>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink to="/" class="nav-item">
          <span>⌘</span>
          <p>总览仪表盘</p>
        </RouterLink>
        <RouterLink to="/chat" class="nav-item">
          <span>◐</span>
          <p>大模型对话</p>
        </RouterLink>
        <RouterLink v-for="item in features" :key="item.key" :to="`/feature/${item.key}`" class="nav-item">
          <span>{{ item.icon }}</span>
          <p>{{ item.title }}</p>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="user-chip">
          <div class="avatar">{{ userInitial }}</div>
          <div>
            <strong>{{ auth.user?.username || 'security-admin' }}</strong>
            <span>{{ auth.user?.roles?.[0] || 'SOC Analyst' }}</span>
          </div>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar glass-card">
        <div>
          <p class="eyebrow">Authorized Security Exercise Platform</p>
          <h1>{{ title }}</h1>
        </div>
        <div class="topbar-actions">
          <span class="status-dot"></span>
          <span>API Connected</span>
        </div>
      </header>
      <section class="content-panel">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { features } from '../services/features'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const userInitial = computed(() => (auth.user?.username || 'S').slice(0, 1).toUpperCase())
const title = computed(() => {
  if (route.name === 'chat') return '大模型安全智库对话'
  const matched = features.find((item) => item.key === route.params.key)
  return matched?.title || '攻防演练仪表盘'
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
