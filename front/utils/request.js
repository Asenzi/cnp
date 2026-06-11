const LOCAL_DEV_BASE_URL = 'http://127.0.0.1:8001'
const LAN_DEV_BASE_URL = 'http://172.20.10.3:8001'
const DEFAULT_PROD_BASE_URL = 'https://www.cnptec.site'
const API_BASE_URL_STORAGE_KEY = '__API_BASE_URL__'
const API_DEBUG_RECORD_STORAGE_KEY = '__LAST_API_DEBUG__'
const API_BASE_URL_ENV_KEYS = ['VUE_APP_API_BASE_URL', 'UNI_APP_API_BASE_URL', 'API_BASE_URL']
const STALE_DEV_BASE_URLS = new Set([
  'http://192.168.12.131:8001'
])

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
  if (STALE_DEV_BASE_URLS.has(normalized)) {
    return getDefaultDevBaseUrl()
  }
  if (/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(normalized)) {
    return LOCAL_DEV_BASE_URL
  }
  return normalized
}

function getRuntimePlatform() {
  try {
    return String(uni.getSystemInfoSync()?.platform || '').trim().toLowerCase()
  } catch (error) {
    return ''
  }
}

function getMiniProgramEnvVersion() {
  try {
    if (typeof __wxConfig !== 'undefined' && __wxConfig) {
      return String(__wxConfig.envVersion || '').trim().toLowerCase()
    }
  } catch (error) {
    // Ignore runtime probing failures.
  }

  try {
    if (typeof globalThis !== 'undefined' && globalThis.__wxConfig) {
      return String(globalThis.__wxConfig.envVersion || '').trim().toLowerCase()
    }
  } catch (error) {
    // Ignore runtime probing failures.
  }

  return ''
}

function isWechatDevelopRuntime() {
  return getMiniProgramEnvVersion() === 'develop'
}

function isWechatPublishedRuntime() {
  return ['trial', 'release'].includes(getMiniProgramEnvVersion())
}

function getDefaultDevBaseUrl() {
  return LAN_DEV_BASE_URL
}

function getNodeEnv() {
  return String(getProcessEnv().NODE_ENV || '').trim().toLowerCase()
}

function isDevelopmentEnv() {
  const nodeEnv = getNodeEnv()
  return nodeEnv === 'development' || nodeEnv === 'dev'
}

function isProductionEnv() {
  const nodeEnv = getNodeEnv()
  return nodeEnv === 'production' || nodeEnv === 'prod'
}

function isHttpsBaseUrl(url) {
  return /^https:\/\//i.test(normalizeBaseUrl(url))
}

function resolveApiBaseUrlFromEnv(options = {}) {
  const allowHttp = Boolean(options.allowHttp)
  const env = getProcessEnv()
  for (const key of API_BASE_URL_ENV_KEYS) {
    const value = normalizeUnsafeLoopback(env[key])
    if (value && (allowHttp || isHttpsBaseUrl(value))) {
      return value
    }
  }
  return ''
}

export function getSuggestedApiBaseUrl() {
  const envBaseUrl = resolveApiBaseUrlFromEnv({
    allowHttp: isDevelopmentEnv() || isWechatDevelopRuntime()
  })
  if (envBaseUrl) {
    return envBaseUrl
  }

  if (isDevelopmentEnv()) {
    const customBaseUrl = normalizeUnsafeLoopback(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
    if (customBaseUrl) {
      return customBaseUrl
    }
  }

  return getBaseUrl()
}

function getBaseUrl() {
  // Development:
  // 1) Runtime override via storage
  // 2) Build-time env
  // 3) Development fallback
  //
  // Production:
  // 1) Build-time env
  // 2) Production fallback
  //
  // This keeps local debugging and production deployment clearly separated,
  // and avoids stale runtime overrides leaking into production requests.
  if (isWechatPublishedRuntime()) {
    return DEFAULT_PROD_BASE_URL
  }

  if (isDevelopmentEnv() || isWechatDevelopRuntime()) {
    const customBaseUrl = normalizeUnsafeLoopback(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
    if (customBaseUrl) {
      return customBaseUrl
    }
  }

  const envBaseUrl = resolveApiBaseUrlFromEnv({
    allowHttp: isDevelopmentEnv() || isWechatDevelopRuntime()
  })
  if (envBaseUrl) {
    return envBaseUrl
  }

  if (isDevelopmentEnv() || isWechatDevelopRuntime()) {
    return getDefaultDevBaseUrl()
  }

  if (isProductionEnv()) {
    return DEFAULT_PROD_BASE_URL
  }

  // Uploaded trial builds can have an empty NODE_ENV, so unknown runtime must
  // prefer production HTTPS instead of leaking a local LAN address.
  const platform = getRuntimePlatform()
  if (platform === 'devtools') {
    return getDefaultDevBaseUrl()
  }
  return DEFAULT_PROD_BASE_URL
}

export function getApiBaseUrl() {
  return getBaseUrl()
}

export function getApiEnvInfo() {
  return {
    nodeEnv: getNodeEnv(),
    envVersion: getMiniProgramEnvVersion(),
    baseUrl: getBaseUrl(),
    envBaseUrl: resolveApiBaseUrlFromEnv({
      allowHttp: isDevelopmentEnv() || isWechatDevelopRuntime()
    }),
    runtimeOverride: (isDevelopmentEnv() || isWechatDevelopRuntime())
      ? normalizeUnsafeLoopback(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
      : '',
    isDevelopment: isDevelopmentEnv(),
    isProduction: isProductionEnv() || isWechatPublishedRuntime()
  }
}

function writeApiDebugRecord(stage, payload = {}) {
  const record = {
    ts: Date.now(),
    stage,
    nodeEnv: getNodeEnv(),
    envVersion: getMiniProgramEnvVersion(),
    baseUrl: getBaseUrl(),
    envBaseUrl: resolveApiBaseUrlFromEnv({
      allowHttp: isDevelopmentEnv() || isWechatDevelopRuntime()
    }),
    runtimeOverride: normalizeUnsafeLoopback(uni.getStorageSync(API_BASE_URL_STORAGE_KEY)),
    ...payload
  }

  try {
    if (typeof globalThis !== 'undefined') {
      globalThis.__LAST_API_DEBUG__ = record
    }
  } catch (error) {
    // Ignore global assignment failures during debugging.
  }

  try {
    uni.setStorageSync(API_DEBUG_RECORD_STORAGE_KEY, record)
  } catch (error) {
    // Ignore storage write failures during debugging.
  }

  console.warn('[API DEBUG]', record)
  return record
}

export function getLastApiDebugRecord() {
  try {
    return uni.getStorageSync(API_DEBUG_RECORD_STORAGE_KEY) || null
  } catch (error) {
    return null
  }
}

export function clearLastApiDebugRecord() {
  try {
    uni.removeStorageSync(API_DEBUG_RECORD_STORAGE_KEY)
  } catch (error) {
    // Ignore storage clear failures during debugging.
  }
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

  const finalUrl = normalizeUrl(url)
  writeApiDebugRecord('request', {
    finalUrl,
    method
  })

  return new Promise((resolve, reject) => {
    uni.request({
      url: finalUrl,
      method,
      data,
      header: headers,
      success: (res) => {
        const payload = res?.data || {}
        const statusCode = res?.statusCode || 500

        writeApiDebugRecord('response', {
          finalUrl,
          method,
          statusCode,
          responseCode: payload?.code ?? null,
          responseMessage: payload?.message || ''
        })

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
        writeApiDebugRecord('fail', {
          finalUrl,
          method,
          errorMessage: err?.errMsg || 'Network error'
        })

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
