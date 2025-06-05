import axios from 'axios'
import { API_BASE_URL } from './apiConstants'

// 创建axios实例
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {    // 统一错误处理
    if (error.response?.status === 401) {
      // 处理未授权错误
      localStorage.removeItem('access_token')
      localStorage.removeItem('userInfo')
      // 可以重定向到登录页
    }
    return Promise.reject(error)
  }
)

export default apiClient