import { getApiBaseUrl, request } from '../utils/request'

function buildQuery(params = {}) {
  const query = []
  Object.keys(params).forEach((key) => {
    const value = params[key]
    if (value === undefined || value === null || value === '') {
      return
    }
    query.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  })
  return query.join('&')
}

export function getImOverview() {
  return request({
    url: '/api/v1/im/overview',
    method: 'GET'
  })
}

export function getImConversations(params = {}) {
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/im/conversations${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function getConversationMessages(targetUserId, params = {}) {
  const target = encodeURIComponent(String(targetUserId || '').trim())
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/im/conversations/${target}/messages${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function sendConversationMessage(targetUserId, payload = {}) {
  const target = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/im/conversations/${target}/messages`,
    method: 'POST',
    data: {
      content: String(payload.content || '').trim(),
      content_type: String(payload.content_type || 'text').trim() || 'text'
    }
  })
}

export function markConversationRead(targetUserId) {
  const target = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/im/conversations/${target}/read`,
    method: 'POST'
  })
}

export function revokeConversationMessage(targetUserId, messageId) {
  const target = encodeURIComponent(String(targetUserId || '').trim())
  const message = encodeURIComponent(String(messageId || '').trim())
  return request({
    url: `/api/v1/im/conversations/${target}/messages/${message}/revoke`,
    method: 'POST'
  })
}

export function getFriendRequests(params = {}) {
  const query = buildQuery({
    tab: String(params.tab || 'pending').trim(),
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/im/friend-requests${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function createFriendRequest(payload = {}) {
  return request({
    url: '/api/v1/im/friend-requests',
    method: 'POST',
    data: {
      target_user_id: String(payload.target_user_id || '').trim(),
      message: String(payload.message || '').trim()
    }
  })
}

export function acceptFriendRequest(requestId) {
  return request({
    url: `/api/v1/im/friend-requests/${encodeURIComponent(String(requestId || ''))}/accept`,
    method: 'POST'
  })
}

export function ignoreFriendRequest(requestId) {
  return request({
    url: `/api/v1/im/friend-requests/${encodeURIComponent(String(requestId || ''))}/ignore`,
    method: 'POST'
  })
}

export function getSystemNotices(params = {}) {
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/im/system-notices${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function getImPresence(targetUserId) {
  const target = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/im/presence/${target}`,
    method: 'GET'
  })
}

export function getImWebSocketUrl() {
  const httpBase = String(getApiBaseUrl() || 'http://172.20.10.3:8001').trim().replace(/\/$/, '')
  if (httpBase.startsWith('https://')) {
    return `${httpBase.replace(/^https:\/\//, 'wss://')}/api/v1/im/ws`
  }
  if (httpBase.startsWith('http://')) {
    return `${httpBase.replace(/^http:\/\//, 'ws://')}/api/v1/im/ws`
  }
  return `ws://${httpBase}/api/v1/im/ws`
}

export function uploadImAsset(filePath, options = {}) {
  const safePath = String(filePath || '').trim()
  if (!safePath) {
    return Promise.reject({
      statusCode: 0,
      code: -1,
      message: '文件路径不能为空',
      payload: null
    })
  }

  const kind = String(options.kind || 'image').trim() || 'image'
  const name = String(options.name || '').trim() || 'file'
  const token = uni.getStorageSync('token')
  const baseUrl = String(getApiBaseUrl() || 'http://172.20.10.3:8001').replace(/\/$/, '')
  const uploadUrl = `${baseUrl}/api/v1/im/assets/upload?kind=${encodeURIComponent(kind)}`
  const header = token
    ? {
      Authorization: `Bearer ${token}`
    }
    : {}

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: uploadUrl,
      filePath: safePath,
      name: 'file',
      fileName: name,
      header,
      success: (res) => {
        const statusCode = Number(res?.statusCode || 500)
        let payload = {}
        try {
          payload = JSON.parse(String(res?.data || '{}'))
        } catch (err) {
          payload = {}
        }

        if (statusCode >= 200 && statusCode < 300 && payload?.code === 0) {
          resolve(payload.data || {})
          return
        }

        reject({
          statusCode,
          code: payload?.code ?? statusCode,
          message: payload?.message || `Request failed: ${statusCode}`,
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
