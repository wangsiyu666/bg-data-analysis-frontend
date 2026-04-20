import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useGlobalStore } from '@/stores/global'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const MOCK_FALLBACK = import.meta.env.VITE_MOCK_FALLBACK === 'true'

export const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 20000
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
  return config
})

request.interceptors.response.use(
  (res) => {
    if (!res.config.hideLoading) stopLoading()
    const body = res.data
    if (body && typeof body === 'object' && 'code' in body && body.code !== 0 && body.code !== 200) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body?.data !== undefined ? body.data : body
  },
  (error) => {
    stopLoading()
    ElMessage.error(error.message || '网络错误')
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
        console.warn('[api fallback]', e?.message)
        return withMock()
      }
      throw e
    }
  }
}

export default request
