import { defineStore } from 'pinia'
import api from '../services/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    activeSessionId: '',
    messages: [],
    loadingSessions: false,
    sending: false,
  }),
  getters: {
    activeSession: (state) => state.sessions.find((item) => item.id === state.activeSessionId),
  },
  actions: {
    async loadSessions() {
      this.loadingSessions = true
      try {
        const { data } = await api.get('/v1/chat/sessions')
        this.sessions = data
        if (!this.activeSessionId && this.sessions.length) {
          this.activeSessionId = this.sessions[0].id
        }
        return data
      } finally {
        this.loadingSessions = false
      }
    },
    async createSession(payload = {}) {
      const { data } = await api.post('/v1/chat/sessions', payload)
      this.sessions = [data, ...this.sessions]
      this.activeSessionId = data.id
      this.messages = []
      return data
    },
    async loadMessages(sessionId = this.activeSessionId) {
      if (!sessionId) {
        this.messages = []
        return []
      }
      const { data } = await api.get(`/v1/chat/sessions/${sessionId}/messages`)
      this.activeSessionId = sessionId
      this.messages = data
      return data
    },
    async sendChat(payload) {
      this.sending = true
      const optimisticUser = {
        id: `local-${Date.now()}`,
        role: 'user',
        content: payload.question,
        mode: payload.mode,
        created_at: new Date().toISOString(),
        payload: {
          assets: payload.assets || [],
          evidence: payload.evidence || [],
        },
      }
      this.messages.push(optimisticUser)
      try {
        const { data } = await api.post('/v1/chat', payload)
        if (data.session_id) {
          this.activeSessionId = data.session_id
        }
        const assistant = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          mode: data.mode,
          created_at: new Date().toISOString(),
          payload: data,
        }
        this.messages.push(assistant)
        await this.loadSessions()
        if (this.activeSessionId) {
          await this.loadMessages(this.activeSessionId)
        }
        return data
      } finally {
        this.sending = false
      }
    },
  },
})
