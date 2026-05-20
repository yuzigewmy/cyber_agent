import axios from 'axios'

const defaultApiBaseUrl =
  typeof window === 'undefined' ? '' : `${window.location.protocol}//${window.location.hostname}:8000`

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl,
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cyber_agent_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('cyber_agent_token')
      localStorage.removeItem('cyber_agent_user')
    }
    return Promise.reject(error)
  },
)

export default api
