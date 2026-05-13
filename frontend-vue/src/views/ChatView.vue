<template>
  <div class="chat-layout">
    <aside class="conversation-panel glass-card">
      <button class="primary-button full" @click="newSession">新建会话</button>
      <div class="conversation-list">
        <button
          v-for="session in chat.sessions"
          :key="session.id"
          class="conversation-item"
          :class="{ active: session.id === chat.activeSessionId }"
          @click="selectSession(session.id)"
        >
          <strong>{{ session.title }}</strong>
          <span>{{ modeLabel(session.mode) }} · {{ formatTime(session.updated_at) }}</span>
        </button>
        <p v-if="!chat.sessions.length" class="empty-text">暂无历史会话，开始第一次安全研判。</p>
      </div>
    </aside>

    <section class="chat-main glass-card">
      <div class="chat-toolbar">
        <div>
          <p class="eyebrow">LLM Chat</p>
          <h2>和大模型交互</h2>
        </div>
        <select v-model="form.mode">
          <option value="defense">防守方</option>
          <option value="threat_intel">威胁情报</option>
          <option value="redteam">授权红队</option>
        </select>
      </div>

      <div class="message-stream" ref="streamRef">
        <article v-for="message in chat.messages" :key="message.id" class="message" :class="message.role">
          <div class="message-avatar">{{ message.role === 'user' ? '你' : 'AI' }}</div>
          <div class="message-bubble">
            <div class="message-meta">
              <strong>{{ message.role === 'user' ? '安全分析员' : 'Cyber Agent' }}</strong>
              <span>{{ formatTime(message.created_at) }}</span>
            </div>
            <p class="message-content">{{ message.content }}</p>
            <div v-if="message.payload?.findings?.length" class="result-block">
              <strong>Findings</strong>
              <ul>
                <li v-for="finding in message.payload.findings" :key="finding.title">
                  {{ finding.severity }} · {{ finding.title }}
                </li>
              </ul>
            </div>
            <div v-if="message.payload?.actions?.length" class="result-block">
              <strong>Actions</strong>
              <ul>
                <li v-for="action in message.payload.actions" :key="action">{{ action }}</li>
              </ul>
            </div>
          </div>
        </article>
        <div v-if="!chat.messages.length" class="chat-empty">
          <div class="empty-icon">◐</div>
          <h3>开始一次安全智库对话</h3>
          <p>选择模式，填写资产和证据，Agent 会结合 RAG 知识库、策略门禁和工具模块输出可追溯建议。</p>
        </div>
      </div>

      <form class="composer" @submit.prevent="send">
        <div class="composer-grid">
          <label>
            <span>资产范围</span>
            <input v-model="form.assets" placeholder="api-gateway, user-service" />
          </label>
          <label>
            <span>证据 / 日志</span>
            <input v-model="form.evidence" placeholder="GET /.env, 401 burst, suspicious IP" />
          </label>
        </div>
        <div v-if="form.mode === 'redteam'" class="scope-box">
          <label class="check-line">
            <input v-model="form.scope.approved" type="checkbox" />
            <span>已获得授权审批</span>
          </label>
          <input v-model="form.scope.approver" placeholder="审批人，例如 ciso / exercise-lead" />
          <input v-model="form.scope.ticket_id" placeholder="审批单号 / 工单号" />
        </div>
        <div class="prompt-row">
          <textarea v-model="form.question" rows="3" placeholder="输入你的问题，例如：请研判这些可疑流量并给出处置建议。"></textarea>
          <button class="primary-button send-button" :disabled="chat.sending || !form.question.trim()">
            {{ chat.sending ? '生成中...' : '发送' }}
          </button>
        </div>
        <p v-if="error" class="error-text">{{ error }}</p>
      </form>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '../stores/chat'

const route = useRoute()
const chat = useChatStore()
const streamRef = ref(null)
const error = ref('')
const form = reactive({
  mode: route.query.mode || 'defense',
  question: route.query.prompt || '',
  assets: 'api-gateway, user-service',
  evidence: 'GET /.env 404, GET /login?user=admin or 1=1',
  scope: {
    approved: false,
    approver: '',
    ticket_id: '',
    time_window: '',
    rules_of_engagement: 'Authorized internal exercise. High-level planning only.',
  },
})

onMounted(async () => {
  await chat.loadSessions()
  if (chat.activeSessionId) await chat.loadMessages(chat.activeSessionId)
  scrollToBottom()
})

watch(() => chat.messages.length, () => scrollToBottom())

async function newSession() {
  await chat.createSession({ title: 'New conversation', mode: form.mode })
}

async function selectSession(id) {
  await chat.loadMessages(id)
}

async function send() {
  error.value = ''
  try {
    await chat.sendChat({
      mode: form.mode,
      question: form.question,
      assets: splitList(form.assets),
      evidence: splitList(form.evidence),
      session_id: chat.activeSessionId || null,
      scope: form.scope,
    })
    form.question = ''
  } catch (err) {
    error.value = err?.response?.data?.detail || '请求失败，请检查后端服务或登录状态。'
  }
}

function splitList(value) {
  return String(value || '')
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function scrollToBottom() {
  nextTick(() => {
    const el = streamRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function modeLabel(mode) {
  return { defense: '防守', threat_intel: '情报', redteam: '红队' }[mode] || mode
}

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
</script>
