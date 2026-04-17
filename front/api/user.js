import { getApiBaseUrl, request } from '../utils/request'

export function getCurrentUserProfile() {
  return request({
    url: '/api/v1/user/me',
    method: 'GET'
  })
}

export function getUserProfileById(targetUserId) {
  const safeId = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/user/profiles/${safeId}`,
    method: 'GET'
  })
}

export function updateCurrentUserProfile(payload) {
  return request({
    url: '/api/v1/user/me',
    method: 'PATCH',
    data: payload || {}
  })
}

export function uploadCurrentUserAvatar(filePath) {
  const token = uni.getStorageSync('token')
  const headers = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getApiBaseUrl()}/api/v1/user/me/avatar`,
      filePath,
      name: 'file',
      header: headers,
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

export function uploadCurrentUserCardFile(filePath, fileName = 'card-file') {
  const token = uni.getStorageSync('token')
  const headers = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getApiBaseUrl()}/api/v1/user/me/card-file`,
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

export function getCurrentUserPrivacySettings() {
  return request({
    url: '/api/v1/user/me/privacy',
    method: 'GET'
  })
}

export function updateCurrentUserPrivacySettings(payload) {
  return request({
    url: '/api/v1/user/me/privacy',
    method: 'PATCH',
    data: payload || {}
  })
}

export function getBlockedUsers(params = {}) {
  const offset = Number(params.offset || 0)
  const limit = Number(params.limit || 20)
  return request({
    url: `/api/v1/user/me/blocked-users?offset=${Math.max(offset, 0)}&limit=${Math.max(limit, 1)}`,
    method: 'GET'
  })
}

export function addBlockedUser(targetUserId) {
  return request({
    url: '/api/v1/user/me/blocked-users',
    method: 'POST',
    data: {
      target_user_id: String(targetUserId || '').trim()
    }
  })
}

export function removeBlockedUser(targetUserId) {
  const normalized = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/user/me/blocked-users/${normalized}`,
    method: 'DELETE'
  })
}
