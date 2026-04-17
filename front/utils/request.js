const DEFAULT_LOOPBACK_BASE_URL = 'http://172.20.10.3:8001'
const DEV_FALLBACK_BASE_URL = DEFAULT_LOOPBACK_BASE_URL
const PROD_FALLBACK_BASE_URL = DEFAULT_LOOPBACK_BASE_URL
const API_BASE_URL_STORAGE_KEY = '__API_BASE_URL__'
const API_BASE_URL_ENV_KEYS = ['VUE_APP_API_BASE_URL', 'UNI_APP_API_BASE_URL', 'API_BASE_URL']

function getProcessEnv() {
  if (typeof process !== 'undefined' && process && process.env) {
    return process.env
  }
  return {}
}

function normalizeBaseUrl(url) {
  if (typeof url !== 'string') {
    return ''
  }
  return url.trim().replace(/\/$/, '')
}

function normalizeUnsafeLoopback(url) {
  const normalized = normalizeBaseUrl(url)
  if (!normalized) {
    return ''
  }
  if (/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(normalized)) {
    return DEV_FALLBACK_BASE_URL
  }
  return normalized
}

function resolveApiBaseUrlFromEnv() {
  const env = getProcessEnv()
  for (const key of API_BASE_URL_ENV_KEYS) {
    const value = normalizeUnsafeLoopback(env[key])
    if (value) {
      return value
    }
  }
  return ''
}

export function getSuggestedApiBaseUrl() {
  const envBaseUrl = resolveApiBaseUrlFromEnv()
  if (envBaseUrl) {
    return envBaseUrl
  }

  const customBaseUrl = normalizeUnsafeLoopback(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
  if (customBaseUrl) {
    return customBaseUrl
  }

  return getBaseUrl()
}

function getBaseUrl() {
  // Priority:
  // 1) Runtime override via storage (handy for fast LAN switching)
  // 2) Build-time env (recommended for team/dev/prod consistency)
  // 3) Hardcoded fallback
  const customBaseUrl = normalizeUnsafeLoopback(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
  if (customBaseUrl) {
    return customBaseUrl
  }

  const envBaseUrl = resolveApiBaseUrlFromEnv()
  if (envBaseUrl) {
    return envBaseUrl
  }

  if (getProcessEnv().NODE_ENV === 'development') {
    return DEV_FALLBACK_BASE_URL
  }

  return PROD_FALLBACK_BASE_URL
}

export function getApiBaseUrl() {
  return getBaseUrl()
}

function normalizeUrl(url) {
  if (/^https?:\/\//.test(url)) {
    return url
  }
  if (url.startsWith('/')) {
    return `${getBaseUrl()}${url}`
  }
  return `${getBaseUrl()}/${url}`
}

export function request(options) {
  const {
    url,
    method = 'GET',
    data,
    header = {}
  } = options || {}

  const token = uni.getStorageSync('token')
  const headers = {
    'Content-Type': 'application/json',
    ...header
  }

  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: normalizeUrl(url),
      method,
      data,
      header: headers,
      success: (res) => {
        const payload = res?.data || {}
        const statusCode = res?.statusCode || 500

        if (statusCode >= 200 && statusCode < 300 && payload?.code === 0) {
          resolve(payload.data)
          return
        }

        const message = payload?.message || `Request failed: ${statusCode}`
        reject({
          statusCode,
          code: payload?.code ?? statusCode,
          message,
          payload
        })
      },
      fail: (err) => {
        reject({
          statusCode: 0,
          code: -1,
          message: err?.errMsg || 'Network error',
          payload: err
        })
      }
    })
  })
}

export function setApiBaseUrl(url) {
  const normalized = normalizeUnsafeLoopback(url)
  if (!normalized) {
    uni.removeStorageSync(API_BASE_URL_STORAGE_KEY)
    return
  }
  uni.setStorageSync(API_BASE_URL_STORAGE_KEY, normalized)
}

export function clearApiBaseUrl() {
  uni.removeStorageSync(API_BASE_URL_STORAGE_KEY)
}

