import { getApiBaseUrl, request } from '../utils/request'

export function createCircle(payload) {
  return request({
    url: '/api/v1/circle',
    method: 'POST',
    data: payload || {}
  })
}

export function updateCircle(circleCode, payload) {
  const safeCode = encodeURIComponent(String(circleCode || '').trim())
  return request({
    url: `/api/v1/circle/${safeCode}`,
    method: 'PATCH',
    data: payload || {}
  })
}

export function getCircleDetail(circleCode) {
  const safeCode = encodeURIComponent(String(circleCode || '').trim())
  return request({
    url: `/api/v1/circle/${safeCode}`,
    method: 'GET'
  })
}

export function getCirclePosts(circleCode, params = {}) {
  const safeCode = encodeURIComponent(String(circleCode || '').trim())
  const cursor = String(params.cursor || '').trim()
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)
  const query = [`limit=${limit}`]
  if (cursor) {
    query.push(`cursor=${encodeURIComponent(cursor)}`)
  }
  return request({
    url: `/api/v1/circle/${safeCode}/posts?${query.join('&')}`,
    method: 'GET'
  })
}

export function getPendingCirclePostSyncs(circleCode) {
  const safeCode = encodeURIComponent(String(circleCode || '').trim())
  return request({
    url: `/api/v1/circle/${safeCode}/post-syncs/pending`,
    method: 'GET'
  })
}

export function reviewCirclePostSync(circleCode, syncId, payload = {}) {
  const safeCode = encodeURIComponent(String(circleCode || '').trim())
  const safeSyncId = encodeURIComponent(String(syncId || '').trim())
  return request({
    url: `/api/v1/circle/${safeCode}/post-syncs/${safeSyncId}/review`,
    method: 'POST',
    data: {
      action: String(payload.action || '').trim(),
      reject_reason: String(payload.reject_reason || '').trim()
    }
  })
}

export function getDiscoverCircles(params = {}) {
  const query = []
  const appendQuery = (key, value) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    query.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  }

  const tab = String(params.tab || 'recommend').trim()
  const offset = Math.max(Number(params.offset || 0), 0)
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)
  const keyword = String(params.keyword || '').trim()
  const cityName = String(params.city_name || '').trim()
  const industryLabel = String(params.industry_label || '').trim()
  const requestId = String(params.request_id || '').trim()
  const excludeCircleCodes = Array.isArray(params.exclude_circle_codes)
    ? params.exclude_circle_codes.map((code) => String(code || '').trim()).filter(Boolean).join(',')
    : String(params.exclude_circle_codes || '').trim()
  appendQuery('tab', tab)
  appendQuery('offset', offset)
  appendQuery('limit', limit)
  appendQuery('keyword', keyword)
  appendQuery('city_name', cityName)
  appendQuery('industry_label', industryLabel)
  appendQuery('request_id', requestId)
  appendQuery('exclude_circle_codes', excludeCircleCodes)
  return request({
    url: `/api/v1/circle/discover?${query.join('&')}`,
    method: 'GET'
  })
}

export function getMyCircles(params = {}) {
  const offset = Math.max(Number(params.offset || 0), 0)
  const limit = Math.max(Number(params.limit || 20), 1)
  const keyword = String(params.keyword || '').trim()
  const query = [`offset=${offset}`, `limit=${limit}`]
  if (keyword) {
    query.push(`keyword=${encodeURIComponent(keyword)}`)
  }
  return request({
    url: `/api/v1/circle/me?${query.join('&')}`,
    method: 'GET'
  })
}

export function getUserCircles(targetUserId, params = {}) {
  const safeTargetUserId = encodeURIComponent(String(targetUserId || '').trim())
  const offset = Math.max(Number(params.offset || 0), 0)
  const limit = Math.max(Number(params.limit || 20), 1)
  const keyword = String(params.keyword || '').trim()
  const query = [`offset=${offset}`, `limit=${limit}`]
  if (keyword) {
    query.push(`keyword=${encodeURIComponent(keyword)}`)
  }
  return request({
    url: `/api/v1/circle/user/${safeTargetUserId}?${query.join('&')}`,
    method: 'GET'
  })
}

export function uploadCircleImage(filePath, fileName = 'circle-image') {
  const token = uni.getStorageSync('token')
  const headers = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getApiBaseUrl()}/api/v1/circle/cover-file`,
      filePath,
      name: 'file',
      header: headers,
      formData: {
        file_name: fileName
      },
      success: (res) => {
        const statusCode = res?.statusCode || 500
        let payload = {}

        try {
          payload = JSON.parse(res?.data || '{}')
        } catch (err) {
          payload = {}
        }

        if (statusCode >= 200 && statusCode < 300 && payload?.code === 0) {
          resolve(payload.data)
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

export function uploadCircleCover(filePath, fileName = 'circle-cover') {
  return uploadCircleImage(filePath, fileName)
}

export function uploadCircleAvatar(filePath, fileName = 'circle-avatar') {
  return uploadCircleImage(filePath, fileName)
}
