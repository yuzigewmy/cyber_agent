const config = window.CYBER_AGENT_CONFIG || {}

const API_BASE_URL =
  config.API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`

const API_TOKEN = config.TOKEN || localStorage.getItem('cyber_agent_token') || ''

const elements = {
  messages: document.getElementById('messages'),
  questionInput: document.getElementById('questionInput'),
  sendButton: document.getElementById('sendButton'),
  clearButton: document.getElementById('clearButton'),
  modeSelect: document.getElementById('modeSelect'),
  assetsInput: document.getElementById('assetsInput'),
  evidenceInput: document.getElementById('evidenceInput'),
  apiStatus: document.getElementById('apiStatus'),
  apiBaseText: document.getElementById('apiBaseText'),
}

let sending = false

function splitLines(value) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function escapeHTML(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function formatText(value) {
  const safe = escapeHTML(value || '')

  return safe
    .replace(/^### (.*)$/gm, '<h4>$1</h4>')
    .replace(/^## (.*)$/gm, '<h3>$1</h3>')
    .replace(/^# (.*)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br />')
}

function scrollToBottom() {
  elements.messages.scrollTop = elements.messages.scrollHeight
}

function removeWelcomeCard() {
  const welcome = elements.messages.querySelector('.welcome-card')
  if (welcome) {
    welcome.remove()
  }
}

function addUserMessage(text) {
  removeWelcomeCard()

  const node = document.createElement('article')
  node.className = 'message user-message'
  node.innerHTML = `
    <div class="message-avatar">你</div>
    <div class="message-body">
      <div class="message-content">${formatText(text)}</div>
    </div>
  `

  elements.messages.appendChild(node)
  scrollToBottom()
}

function addLoadingMessage() {
  removeWelcomeCard()

  const node = document.createElement('article')
  node.className = 'message assistant-message loading-message'
  node.id = 'loadingMessage'
  node.innerHTML = `
    <div class="message-avatar">AI</div>
    <div class="message-body">
      <div class="message-content">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `

  elements.messages.appendChild(node)
  scrollToBottom()
}

function removeLoadingMessage() {
  const node = document.getElementById('loadingMessage')
  if (node) {
    node.remove()
  }
}

function renderList(title, items) {
  if (!items || !items.length) {
    return ''
  }

  const list = items
    .map((item) => `<li>${formatText(item)}</li>`)
    .join('')

  return `
    <section class="result-section">
      <h4>${escapeHTML(title)}</h4>
      <ul>${list}</ul>
    </section>
  `
}

function renderFindings(findings) {
  if (!findings || !findings.length) {
    return ''
  }

  const cards = findings
    .map((finding) => {
      const evidence = Array.isArray(finding.evidence)
        ? finding.evidence.map((item) => `<li>${escapeHTML(item)}</li>`).join('')
        : ''

      const mapping = Array.isArray(finding.mapping)
        ? finding.mapping.map((item) => `<span>${escapeHTML(item)}</span>`).join('')
        : ''

      return `
        <div class="finding-card">
          <div class="finding-head">
            <strong>${escapeHTML(finding.title || '安全发现')}</strong>
            <em>${escapeHTML(finding.severity || 'info')}</em>
          </div>

          ${
            mapping
              ? `<div class="tag-list">${mapping}</div>`
              : ''
          }

          ${
            evidence
              ? `<div class="mini-block"><b>证据</b><ul>${evidence}</ul></div>`
              : ''
          }

          ${
            finding.recommendation
              ? `<p>${formatText(finding.recommendation)}</p>`
              : ''
          }
        </div>
      `
    })
    .join('')

  return `
    <section class="result-section">
      <h4>安全发现</h4>
      <div class="finding-list">${cards}</div>
    </section>
  `
}

function addAssistantMessage(data) {
  removeLoadingMessage()

  const blocked = data.blocked ? '<span class="badge danger">已拦截</span>' : ''
  const severity = data.severity
    ? `<span class="badge">${escapeHTML(data.severity)}</span>`
    : ''

  const citations = Array.isArray(data.citations)
    ? data.citations
    : []

  const policyReasons = Array.isArray(data.policy_reasons)
    ? data.policy_reasons
    : []

  const html = `
    <article class="message assistant-message">
      <div class="message-avatar">AI</div>
      <div class="message-body">
        <div class="message-meta">
          ${severity}
          ${blocked}
          ${
            data.requires_human_approval
              ? '<span class="badge warn">需要人工审批</span>'
              : ''
          }
        </div>

        <div class="message-content">
          ${formatText(data.answer || '后端未返回 answer 字段。')}
        </div>

        ${renderFindings(data.findings)}
        ${renderList('建议动作', data.actions)}
        ${renderList('引用来源', citations)}
        ${renderList('策略原因', policyReasons)}
      </div>
    </article>
  `

  elements.messages.insertAdjacentHTML('beforeend', html)
  scrollToBottom()
}

function addErrorMessage(error) {
  removeLoadingMessage()

  const message =
    error?.message ||
    '请求失败，请检查后端服务、API 地址、CORS 配置或浏览器控制台错误。'

  const node = document.createElement('article')
  node.className = 'message assistant-message'
  node.innerHTML = `
    <div class="message-avatar error-avatar">!</div>
    <div class="message-body">
      <div class="message-content error-box">
        ${formatText(message)}
      </div>
    </div>
  `

  elements.messages.appendChild(node)
  scrollToBottom()
}

function buildPayload(question) {
  const mode = elements.modeSelect.value || 'defense'
  const assets = splitLines(elements.assetsInput.value)
  const evidence = splitLines(elements.evidenceInput.value)

  return {
    mode,
    question,
    assets,
    evidence,
    scope: {
      authorized: mode !== 'redteam',
      approver: '',
      ticket_id: '',
      rules_of_engagement: '',
    },
  }
}

async function sendMessage() {
  if (sending) return

  const question = elements.questionInput.value.trim()

  if (!question) {
    elements.questionInput.focus()
    return
  }

  sending = true
  elements.sendButton.disabled = true
  elements.sendButton.textContent = '发送中...'

  addUserMessage(question)
  addLoadingMessage()

  elements.questionInput.value = ''
  autoResizeTextarea(elements.questionInput)

  try {
    const response = await fetch(`${API_BASE_URL}/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
      },
      body: JSON.stringify(buildPayload(question)),
    })

    let data = null

    try {
      data = await response.json()
    } catch {
      data = null
    }

    if (!response.ok) {
      const detail = data?.detail
      throw new Error(
        `后端请求失败：HTTP ${response.status}${
          detail ? `，${JSON.stringify(detail)}` : ''
        }`
      )
    }

    addAssistantMessage(data || {})
  } catch (error) {
    addErrorMessage(error)
  } finally {
    sending = false
    elements.sendButton.disabled = false
    elements.sendButton.textContent = '发送'
  }
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto'
  textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`
}

async function checkHealth() {
  elements.apiBaseText.textContent = API_BASE_URL

  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    elements.apiStatus.textContent = `后端正常：${data.agent || 'Cyber Agent'}`
    document.body.classList.add('api-ok')
  } catch {
    elements.apiStatus.textContent = '后端未连接'
    document.body.classList.remove('api-ok')
  }
}

function bindEvents() {
  elements.sendButton.addEventListener('click', sendMessage)

  elements.questionInput.addEventListener('input', () => {
    autoResizeTextarea(elements.questionInput)
  })

  elements.questionInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  })

  elements.clearButton.addEventListener('click', () => {
    elements.messages.innerHTML = `
      <div class="welcome-card">
        <div class="welcome-icon">✦</div>
        <h3>开始安全研判</h3>
        <p>
          输入攻击流量、告警日志、资产信息或安全问题，系统会调用后端
          <code>/v1/chat</code>
          接口，并将大模型返回内容展示在这里。
        </p>

        <div class="quick-prompts">
          <button data-prompt="请研判这些流量是否存在攻击行为，并给出处置建议。">
            流量研判
          </button>
          <button data-prompt="请根据资产和证据生成应急响应处置方案。">
            应急响应
          </button>
          <button data-prompt="请分析这些资产可能存在的版本漏洞风险。">
            漏洞分析
          </button>
        </div>
      </div>
    `

    bindQuickPrompts()
  })

  bindQuickPrompts()
}

function bindQuickPrompts() {
  document.querySelectorAll('[data-prompt]').forEach((button) => {
    button.addEventListener('click', () => {
      elements.questionInput.value = button.dataset.prompt || ''
      elements.questionInput.focus()
      autoResizeTextarea(elements.questionInput)
    })
  })
}

function init() {
  bindEvents()
  checkHealth()

  setInterval(checkHealth, 30000)
}

init()