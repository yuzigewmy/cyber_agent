<template>
  <div class="dashboard-grid">
    <section class="hero-panel glass-card">
      <p class="eyebrow">Command Center</p>
      <h2>{{ current.title }}</h2>
      <p>{{ current.description }}</p>
      <div class="hero-actions">
        <RouterLink class="primary-button compact" :to="chatLink">进入对话工作台</RouterLink>
        <RouterLink class="ghost-button compact" to="/chat">查看聊天历史</RouterLink>
      </div>
    </section>

    <section class="metrics-row">
      <div v-for="metric in metrics" :key="metric.label" class="metric-card glass-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <p>{{ metric.hint }}</p>
      </div>
    </section>

    <section class="feature-list glass-card">
      <div class="section-heading">
        <p class="eyebrow">Capabilities</p>
        <h3>功能独立入口</h3>
      </div>
      <div class="feature-cards">
        <RouterLink v-for="item in features" :key="item.key" :to="`/feature/${item.key}`" class="feature-card">
          <div class="feature-icon">{{ item.icon }}</div>
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </div>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { features } from '../services/features'

const route = useRoute()
const current = computed(() => features.find((item) => item.key === route.params.key) || {
  title: '攻防演练仪表盘',
  description: '统一呈现防守、威胁情报、授权红队规划、RAG 知识库和应急响应能力。',
  mode: 'defense',
  prompt: '请帮我分析当前攻防演练的优先事项。',
})

const chatLink = computed(() => ({
  path: '/chat',
  query: {
    mode: current.value.mode,
    prompt: current.value.prompt,
  },
}))

const metrics = [
  { label: 'Agent 模式', value: '3', hint: 'Defense / Threat Intel / Red Team' },
  { label: '策略门禁', value: 'ON', hint: '授权范围、敏感输出、审计闭环' },
  { label: '知识增强', value: 'RAG', hint: '架构、流程、漏洞、演练规则' },
]
</script>
