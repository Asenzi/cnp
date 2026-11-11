const PROD_BASE_URL = 'https://www.cnptec.site'
const DEV_BASE_URL = 'http://127.0.0.1:8001'
const BASE_URL_STORAGE_KEY = '__API_BASE_URL__'

function normalizeBaseUrl(url) {
  if (typeof url !== 'string') {
    return ''
  }
  return url.trim().replace(/\/+$/, '')
}

function getEnvVersion() {
  try {
    const info = wx.getAccountInfoSync()
    return String((info && info.miniProgram && info.miniProgram.envVersion) || '').toLowerCase()
  } catch (error) {
    return ''
  }
}

function isDevelopRuntime() {
  return getEnvVersion() === 'develop'
}

function isPublishedRuntime() {
  return ['trial', 'release'].includes(getEnvVersion())
}

function readRuntimeOverride() {
  try {
    return normalizeBaseUrl(wx.getStorageSync(BASE_URL_STORAGE_KEY))
  } catch (error) {
    return ''
  }
}

export function getBaseUrl() {
  if (isPublishedRuntime()) {
    return PROD_BASE_URL
  }

  if (isDevelopRuntime()) {
    const override = readRuntimeOverride()
    if (override) {
      return override
    }
    return DEV_BASE_URL
  }

  // envVersion 取不到时（如部分工具链）保守走生产，避免把内网地址带上线
  return PROD_BASE_URL
}

export function getApiBaseUrl() {
  return getBaseUrl()
}

export function setApiBaseUrl(url) {
  const normalized = normalizeBaseUrl(url)
  if (!normalized) {
    clearApiBaseUrl()
    return
  }
  try {
    wx.setStorageSync(BASE_URL_STORAGE_KEY, normalized)
  } catch (error) {
    // 忽略写入失败
  }
}

export function clearApiBaseUrl() {
  try {
    wx.removeStorageSync(BASE_URL_STORAGE_KEY)
  } catch (error) {
    // 忽略清理失败
  }
}

export function getApiEnvInfo() {
  return {
    envVersion: getEnvVersion(),
    baseUrl: getBaseUrl(),
    runtimeOverride: readRuntimeOverride(),
    isDevelopment: isDevelopRuntime(),
    isProduction: isPublishedRuntime()
  }
}

function normalizeUrl(url) {
  if (/^https?:\/\//i.test(url)) {
    return url
  }
  if (url.charAt(0) === '/') {
    return `${getBaseUrl()}${url}`
  }
  return `${getBaseUrl()}/${url}`
}

function readToken() {
  try {
    return wx.getStorageSync('token') || ''
  } catch (error) {
    return ''
  }
}

export function request(options) {
  const { url, method = 'GET', data, header = {}, timeout = 20000 } = options || {}

  const headers = {
    'Content-Type': 'application/json',
    ...header
  }

  const token = readToken()
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: normalizeUrl(url),
      method,
      data,
      header: headers,
      timeout,
      success(res) {
        const payload = res && res.data ? res.data : {}
        const statusCode = res && res.statusCode ? res.statusCode : 500

        if (statusCode >= 200 && statusCode < 300 && payload.code === 0) {
          resolve(payload.data)
          return
        }

        reject({
          statusCode,
          code: payload.code === undefined ? statusCode : payload.code,
          message: payload.message || `请求失败（${statusCode}）`,
          payload
        })
      },
      fail(err) {
        reject({
          statusCode: 0,
          code: -1,
          message: (err && err.errMsg) || '网络异常',
          payload: err
        })
      }
    })
  })
}

export default request
