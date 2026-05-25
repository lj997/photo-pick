/**
 * API 基础配置 - Axios 实例，基地址 /api，超时 30 秒
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export default api
