<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from './services/api'

const token = ref(localStorage.getItem('cyber_agent_token') || '')
const user = ref(parseSavedUser(localStorage.getItem('cyber_agent_user')))
const capabilities = ref(null)
const messages = ref([])
const error = ref('')
const loading = ref(false)
const loginLoading = ref(false)

const loginForm = reactive({
  username: 'security-admin',
  password: 'ChangeMe123!',
})

const form = reactive({
  mode: 'defense',
  question: 'Analyze these gateway logs and provide response recommendations.',
  assets: 'api-gateway\nuser-service',
  evidence: 'GET /.env 404 nuclei\nGET /login?user=admin or 1=1 400',
  scopeApproved: false,
  approver: '',
  ticketId: '',
})

const modeMeta = {
  defense: {
    label: 'Defense Triage',
    subtitle: 'Log analysis, impact review, and response guidance for SOC workflows.',
  },
  threat_intel: {
    label: 'Threat Intel',
    subtitle: 'Asset, exposure, and vulnerability intelligence prioritization.',
  },
  redteam: {
    label: 'Authorized Red Team',
    subtitle: 'Approval-gated high-level validation planning only.',
  },
}

const isAuthed = computed(() => Boolean(token.value))
const currentMode = computed(() => modeMeta[form.mode])

function parseSavedUser(value) {
  if (!value) {
    return null
  }

  try {
    return JSON.parse(value)
  } catch {
    localStorage.removeItem('cyber_agent_user')
    localStorage.removeItem('cyber_agent_token')
    token.value = ''
    return null
  }
}

function lines(value) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function saveAuth(loginData) {
  token.value = loginData.access_token
  user.value = {
    username: loginData.username,
    roles: loginData.roles || [],
  }
  localStorage.setItem('cyber_agent_token', token.value)
  localStorage.setItem('cyber_agent_user', JSON.stringify(user.value))
}

function logout() {
  token.value = ''
  user.value = null
  messages.value = []
  capabilities.value = null
  localStorage.removeItem('cyber_agent_token')
  localStorage.removeItem('cyber_agent_user')
}

async function loadCapabilities() {
  try {
    const { data } = await api.get('/v1/system/capabilities')
    capabilities.value = data
  } catch {
    capabilities.value = null
  }
}

async function login() {
  error.value = ''
  loginLoading.value = true
  try {
    const { data } = await api.post('/v1/auth/login', loginForm)
    saveAuth(data)
    await loadCapabilities()
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Login failed. Check backend service and credentials.'
  } finally {
    loginLoading.value = false
  }
}

async function submit() {
  if (!form.question.trim()) {
    error.value = 'Enter an analysis question first.'
    return
  }

  error.value = ''
  loading.value = true

  const payload = {
    mode: form.mode,
    question: form.question.trim(),
    assets: lines(form.assets),
    evidence: lines(form.evidence),
    scope: {
      approved: form.mode === 'redteam' ? form.scopeApproved : false,
      approver: form.approver || null,
      ticket_id: form.ticketId || null,
      rules_of_engagement:
        form.mode === 'redteam' && form.scopeApproved
          ? 'Authorized internal exercise with defensive reporting only.'
          : null,
    },
  }

  messages.value.push({
    role: 'user',
    mode: form.mode,
    content: payload.question,
    assets: payload.assets,
    evidence: payload.evidence,
  })

  try {
    const { data } = await api.post('/v1/chat', payload)
    messages.value.push({
      role: 'assistant',
      content: data.answer,
      blocked: data.blocked,
      severity: data.severity,
      findings: data.findings || [],
      actions: data.actions || [],
      citations: data.citations || [],
      policyReasons: data.policy_reasons || [],
      trace: data.trace || {},
    })
  } catch (err) {
    if (err?.response?.status === 401) {
      logout()
      error.value = 'Session expired. Sign in again.'
    } else {
      error.value = err?.response?.data?.detail || 'Request failed. Check that the backend API is running.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isAuthed.value) {
    loadCapabilities()
  }
})
</script>

<template>
  <main class="console">
    <aside class="side">
      <div class="brand">
        <div class="brand-mark">CA</div>
        <div>
          <strong>Cyber Agent</strong>
          <span>Guarded Console</span>
        </div>
      </div>

      <section class="panel">
        <p class="label">System</p>
        <div class="health">
          <span class="dot" :class="{ online: capabilities }"></span>
          <strong>{{ capabilities ? 'API Online' : 'API Pending' }}</strong>
        </div>
        <div v-if="capabilities" class="kv">
          <span>Graph</span>
          <strong>{{ capabilities.graph_enabled ? 'Enabled' : 'Fallback' }}</strong>
          <span>RAG</span>
          <strong>{{ capabilities.rag_backend }}</strong>
          <span>LLM</span>
          <strong>{{ capabilities.llm_available ? 'Connected' : 'Local rules' }}</strong>
        </div>
      </section>

      <section v-if="capabilities?.tools?.length" class="panel">
        <p class="label">Tools</p>
        <ul class="tools">
          <li v-for="tool in capabilities.tools" :key="tool.name">
            <strong>{{ tool.name }}</strong>
            <span>{{ tool.capability }}</span>
          </li>
        </ul>
      </section>

      <button v-if="isAuthed" class="secondary" @click="logout">Sign out</button>
    </aside>

    <section v-if="!isAuthed" class="login-page">
      <div class="login-card">
        <p class="label">Secure Access</p>
        <h1>Cyber Security Agent Console</h1>
        <p>Lean, fast, and built for security operations testing.</p>
        <label>
          <span>Username</span>
          <input v-model="loginForm.username" autocomplete="username" />
        </label>
        <label>
          <span>Password</span>
          <input v-model="loginForm.password" type="password" autocomplete="current-password" />
        </label>
        <button class="primary" :disabled="loginLoading" @click="login">
          {{ loginLoading ? 'Signing in...' : 'Sign in' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </section>

    <section v-else class="workspace">
      <header class="topbar">
        <div>
          <p class="label">Security Operations</p>
          <h1>{{ currentMode.label }}</h1>
          <p>{{ currentMode.subtitle }}</p>
        </div>
        <div class="user">
          <strong>{{ user?.username }}</strong>
          <span>{{ user?.roles?.[0] || 'Analyst' }}</span>
        </div>
      </header>

      <nav class="mode-tabs" aria-label="Agent mode">
        <button :class="{ active: form.mode === 'defense' }" @click="form.mode = 'defense'">
          Defense
        </button>
        <button
          :class="{ active: form.mode === 'threat_intel' }"
          @click="form.mode = 'threat_intel'"
        >
          Threat Intel
        </button>
        <button :class="{ active: form.mode === 'redteam' }" @click="form.mode = 'redteam'">
          Red Team
        </button>
      </nav>

      <div class="grid">
        <section class="chat">
          <div class="messages">
            <article v-if="messages.length === 0" class="empty">
              Enter a question, scoped assets, and evidence. The agent will return guarded findings,
              actions, policy reasons, and orchestration trace.
            </article>

            <article
              v-for="(message, index) in messages"
              :key="index"
              class="message"
              :class="message.role"
            >
              <div class="message-head">
                <strong>{{ message.role === 'user' ? 'Analyst' : 'Cyber Agent' }}</strong>
                <span v-if="message.severity" class="severity" :class="message.severity">
                  {{ message.severity }}
                </span>
              </div>
              <pre>{{ message.content }}</pre>

              <div v-if="message.findings?.length" class="result">
                <h3>Findings</h3>
                <ul>
                  <li v-for="finding in message.findings" :key="finding.title">
                    <strong>{{ finding.title }}</strong>
                    <span>{{ finding.recommendation }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="message.actions?.length" class="result">
                <h3>Actions</h3>
                <ol>
                  <li v-for="action in message.actions" :key="action">{{ action }}</li>
                </ol>
              </div>

              <div v-if="message.policyReasons?.length" class="result warning">
                <h3>Policy Reasons</h3>
                <ul>
                  <li v-for="reason in message.policyReasons" :key="reason">{{ reason }}</li>
                </ul>
              </div>

              <div v-if="message.trace?.nodes?.length" class="trace">
                {{ message.trace.nodes.join(' -> ') }}
              </div>
            </article>
          </div>
        </section>

        <section class="composer">
          <label>
            <span>Question</span>
            <textarea v-model="form.question" rows="5"></textarea>
          </label>
          <label>
            <span>Assets</span>
            <textarea v-model="form.assets" rows="4"></textarea>
          </label>
          <label>
            <span>Evidence / Logs</span>
            <textarea v-model="form.evidence" rows="7"></textarea>
          </label>

          <div v-if="form.mode === 'redteam'" class="approval">
            <label class="check">
              <input v-model="form.scopeApproved" type="checkbox" />
              <span>Approved scope is available</span>
            </label>
            <input v-model="form.approver" placeholder="Approver" />
            <input v-model="form.ticketId" placeholder="Ticket ID" />
          </div>

          <button class="primary" :disabled="loading" @click="submit">
            {{ loading ? 'Analyzing...' : 'Send to Agent' }}
          </button>
          <p v-if="error" class="error">{{ error }}</p>
        </section>
      </div>
    </section>
  </main>
</template>
