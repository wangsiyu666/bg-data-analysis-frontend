import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useGlobalStore } from '@/stores/global'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const MOCK_FALLBACK = import.meta.env.VITE_MOCK_FALLBACK === 'true'
export const DEFAULT_USER_ID = import.meta.env.VITE_DEFAULT_USER_ID || 'demo'

export const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000
})

let pending = 0
function startLoading() {
  pending++
  if (pending === 1) {
    try {
      useGlobalStore().showLoading()
    } catch (e) {}
  }
}
function stopLoading() {
  pending = Math.max(0, pending - 1)
  if (pending === 0) {
    try {
      useGlobalStore().hideLoading()
    } catch (e) {}
  }
}

request.interceptors.request.use((config) => {
  if (!config.hideLoading) startLoading()
  // POST 请求自动注入 user_id（后端所有 /audience /strategy /execution /publish 等都要求）
  if (config.method && config.method.toLowerCase() === 'post') {
    if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
      if (!('user_id' in config.data)) {
        config.data = { ...config.data, user_id: DEFAULT_USER_ID }
      }
    }
  }
  return config
})

request.interceptors.response.use(
  (res) => {
    if (!res.config.hideLoading) stopLoading()
    const body = res.data
    // 兼容两种响应包装：
    // 1) 后端接口文档描述的"直接返回对象"，如 { sql: ... } / { columns, data, total }
    // 2) 旧 mock 返回的 { code, data, message } 包装
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code !== 0 && body.code !== 200) {
        ElMessage.error(body.message || '请求失败')
        return Promise.reject(new Error(body.message || '请求失败'))
      }
      return body.data !== undefined ? body.data : body
    }
    return body
  },
  (error) => {
    stopLoading()
    const detail = error?.response?.data?.detail || error?.response?.data?.message || error.message
    ElMessage.error(detail || '网络错误')
    return Promise.reject(error)
  }
)

export function createApi(realFn, mockFn, opts = {}) {
  const delay = opts.delay ?? 300
  return async (...args) => {
    const withMock = async () => {
      await new Promise((r) => setTimeout(r, delay))
      return mockFn(...args)
    }
    if (USE_MOCK) return withMock()
    try {
      return await realFn(...args)
    } catch (e) {
      if (MOCK_FALLBACK) {
        console.warn('[api fallback to mock]', e?.message)
        return withMock()
      }
      throw e
    }
  }
}

export default request
