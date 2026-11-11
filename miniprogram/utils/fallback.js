/**
 * 真接口优先 + 本地兜底
 *
 * 规则：
 * 1. 真实请求成功 -> 直接返回，不碰 mock
 * 2. 真实请求失败且判定为「网络层不可达」-> 回落本地数据，并打标记
 * 3. 真实请求失败但属于业务错误（4xx）-> 照常抛出，交给页面做业务处理
 *    （例如 401 需要跳登录，用 mock 盖过去会掩盖问题）
 * 4. globalData.mockEnabled = true 时强制走 mock（联调 / 演示用）
 */

const app = () => getApp()

export function isMockForced() {
  try {
    return Boolean(app().globalData.mockEnabled)
  } catch (err) {
    return false
  }
}

export function isNetworkError(err) {
  const statusCode = Number(err && err.statusCode || 0)
  // statusCode 为 0 表示请求根本没有到达服务端（域名不通 / 超时 / 证书问题）
  if (statusCode === 0) return true
  if (statusCode >= 500) return true
  const msg = String((err && (err.errMsg || err.message)) || '')
  return /request:fail|timeout|ERR_/i.test(msg)
}

/**
 * @param {Function} realFn  真实请求，返回 Promise
 * @param {Function} mockFn  兜底数据，返回 Promise 或同步值
 * @param {Object}   options { onFallback, silent }
 */
export function withFallback(realFn, mockFn, options = {}) {
  if (isMockForced()) {
    markFallback()
    return Promise.resolve(mockFn())
  }

  return Promise.resolve()
    .then(realFn)
    .catch((err) => {
      if (!isNetworkError(err)) {
        throw err
      }
      markFallback()
      if (options.onFallback) {
        options.onFallback(err)
      }
      if (!options.silent) {
        wx.showToast({
          title: '网络不可用，已切换本地数据',
          icon: 'none',
          duration: 1600
        })
      }
      return mockFn(err)
    })
}

let fallbackMarked = false

function markFallback() {
  fallbackMarked = true
  try {
    app().globalData.usingMockData = true
  } catch (err) {
    // ignore
  }
}

export function isUsingMockData() {
  return fallbackMarked
}
