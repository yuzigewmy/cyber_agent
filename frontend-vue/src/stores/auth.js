import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',
    user: {
      username: 'anonymous',
      roles: [
        'SOC Analyst',
        'Incident Commander',
        'Red Team Lead',
      ],
    },
    loading: false,
  }),

  getters: {
    isAuthenticated: () => true,
  },

  actions: {
    async login() {
      return {
        username: this.user.username,
        roles: this.user.roles,
      }
    },

    async register() {
      return {
        username: this.user.username,
        roles: this.user.roles,
      }
    },

    async hydrate() {
      return this.user
    },

    logout() {
      // 无登录模式下不做任何处理
      this.user = {
        username: 'anonymous',
        roles: [
          'SOC Analyst',
          'Incident Commander',
          'Red Team Lead',
        ],
      }
    },
  },
})