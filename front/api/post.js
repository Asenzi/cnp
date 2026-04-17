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

export function getResourceFilters() {
  return request({
    url: '/api/v1/post/filters',
    method: 'GET'
  })
}

export function getResourceFeed(params = {}) {
  const excludePostCodes = Array.isArray(params.exclude_post_codes)
    ? params.exclude_post_codes.map((item) => String(item || '').trim()).filter(Boolean)
    : []
  const query = buildQuery({
    mode: String(params.mode || '').trim(),
    sort: String(params.sort || 'latest').trim(),
    keyword: String(params.keyword || '').trim(),
    industry_label: String(params.industry_label || '').trim(),
    request_id: String(params.request_id || '').trim(),
    exclude_post_codes: excludePostCodes.join(','),
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/post/feed${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function getMyResourceFeed(params = {}) {
  const query = buildQuery({
    status: String(params.status || '').trim(),
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/post/mine${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function getUserResourceFeed(targetUserId, params = {}) {
  const safeTargetUserId = encodeURIComponent(String(targetUserId || '').trim())
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/post/user/${safeTargetUserId}/feed${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function createResourcePost(payload = {}) {
  return request({
    url: '/api/v1/post',
    method: 'POST',
    data: {
      mode: String(payload.mode || 'cooperate').trim(),
      title: String(payload.title || '').trim(),
      description: String(payload.description || '').trim(),
      industry_label: String(payload.industry_label || '').trim(),
      images: Array.isArray(payload.images) ? payload.images : [],
      sync_circle_codes: Array.isArray(payload.sync_circle_codes) ? payload.sync_circle_codes : []
    }
  })
}

export function updateResourcePost(postCode, payload = {}) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}`,
    method: 'PUT',
    data: {
      mode: String(payload.mode || 'cooperate').trim(),
      title: String(payload.title || '').trim(),
      description: String(payload.description || '').trim(),
      industry_label: String(payload.industry_label || '').trim(),
      images: Array.isArray(payload.images) ? payload.images : [],
      sync_circle_codes: Array.isArray(payload.sync_circle_codes) ? payload.sync_circle_codes : []
    }
  })
}

export function getResourceDetail(postCode) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}`,
    method: 'GET'
  })
}

export function reportResourceView(postCode) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}/view`,
    method: 'POST'
  })
}

export function likeResourcePost(postCode) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}/like`,
    method: 'POST'
  })
}

export function unlikeResourcePost(postCode) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}/like`,
    method: 'DELETE'
  })
}

export function deleteResourcePost(postCode) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}`,
    method: 'DELETE'
  })
}

export function setResourcePostStatus(postCode, status) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}/status`,
    method: 'POST',
    data: {
      status: String(status || 'active').trim() || 'active'
    }
  })
}

export function setResourcePostPin(postCode, pinned) {
  const safeCode = encodeURIComponent(String(postCode || '').trim())
  return request({
    url: `/api/v1/post/${safeCode}/pin`,
    method: 'POST',
    data: {
      pinned: Boolean(pinned)
    }
  })
}

export function uploadResourceImage(filePath, fileName = 'resource-image') {
  const token = uni.getStorageSync('token')
  const header = token
    ? { Authorization: `Bearer ${token}` }
    : {}

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getApiBaseUrl()}/api/v1/post/assets/upload`,
      filePath: String(filePath || '').trim(),
      name: 'file',
      fileName: String(fileName || 'resource-image').trim() || 'resource-image',
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
          message: payload?.message || `Upload failed: ${statusCode}`,
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
