<template>
  <main class="login-page">
    <section class="login-hero">
      <div class="orb orb-one"></div>
      <div class="orb orb-two"></div>

      <div class="login-card glass-card">
        <div class="login-logo">A</div>

        <p class="eyebrow center">Cyber Attack-Defense Intelligence</p>

        <h1>{{ isRegister ? '创建账号' : '欢迎回来' }}</h1>

        <p class="muted center">
          {{
            isRegister
              ? '注册企业攻防演练智库控制台账号，进入安全运营工作台。'
              : '登录企业攻防演练智库控制台，继续进行防守研判、应急处置和授权演练规划。'
          }}
        </p>

        <form class="login-form" @submit.prevent="submit">
          <label>
            <span>账号</span>
            <input
              v-model.trim="username"
              autocomplete="username"
              placeholder="security-admin"
            />
          </label>

          <label>
            <span>密码</span>
            <input
              v-model="password"
              type="password"
              :autocomplete="isRegister ? 'new-password' : 'current-password'"
              placeholder="请输入密码"
            />
          </label>

          <p
            v-if="message"
            :class="messageType === 'success' ? 'success-text' : 'error-text'"
          >
            {{ message }}
          </p>

          <button class="primary-button" :disabled="auth.loading">
            {{
              auth.loading
                ? '处理中...'
                : isRegister
                  ? '注册'
                  : '登录'
            }}
          </button>

          <button
            type="button"
            class="ghost-button"
            :disabled="auth.loading"
            @click="toggleMode"
          >
            {{ isRegister ? '已有账号？去登录' : '没有账号？创建账号' }}
          </button>
        </form>

        <div class="login-meta">
          <span v-if="!isRegister">开发默认账号：security-admin</span>
          <span>正式环境请接入企业 SSO / OIDC</span>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const username = ref('security-admin')
const password = ref('ChangeMe123!')
const message = ref('')
const messageType = ref('error')

function toggleMode() {
  isRegister.value = !isRegister.value
  message.value = ''
  messageType.value = 'error'

  if (isRegister.value) {
    username.value = ''
    password.value = ''
  } else {
    username.value = 'security-admin'
    password.value = 'ChangeMe123!'
  }
}

async function submit() {
  message.value = ''
  messageType.value = 'error'

  if (!username.value || !password.value) {
    message.value = '请输入账号和密码。'
    return
  }

  try {
    if (isRegister.value) {
      await auth.register(username.value, password.value)
      messageType.value = 'success'
      message.value = '注册成功，请使用新账号登录。'
      isRegister.value = false
      password.value = ''
      return
    }

    await auth.login(username.value, password.value)
    router.push('/')
  } catch (err) {
    messageType.value = 'error'
    message.value =
      err?.response?.data?.detail ||
      (isRegister.value ? '注册失败，请稍后重试。' : '登录失败，请检查账号和密码。')
  }
}
</script>

<style scoped>
.ghost-button {
  width: 100%;
  border: none;
  background: transparent;
  color: #10a37f;
  cursor: pointer;
  font-size: 14px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  transition: background 0.2s ease;
}

.ghost-button:hover {
  background: rgba(16, 163, 127, 0.08);
}

.ghost-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.success-text {
  color: #10a37f;
  font-size: 14px;
  line-height: 1.5;
  margin: 4px 0 0;
}
</style>