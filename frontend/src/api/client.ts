import axios from 'axios'
import axiosRetry from 'axios-retry'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 配置 axios-retry 重试机制
axiosRetry(client, {
  retries: 3,
  retryDelay: (retryCount) => {
    return Math.min(1000 * Math.pow(2, retryCount - 1), 10000)
  },
  retryCondition: (error) => {
    if (!error.response) return true
    if (error.response.status >= 500 && error.response.status < 600) return true
    if (error.response.status === 429) return true
    if (error.response.status === 408) return true
    return false
  },
  shouldResetTimeout: true,
  onRetry: (retryCount, error, requestConfig) => {
    console.warn(`API 请求重试 (${retryCount}/3):`, {
      url: requestConfig.url,
      method: requestConfig.method,
      error: error.message,
    })
  },
})

// 请求拦截器：添加JWT token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：处理错误
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
