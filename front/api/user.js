import { getApiBaseUrl, request } from '../utils/request'

export function getCurrentUserProfile() {
  return request({
    url: '/api/v1/user/me',
    method: 'GET'
  })
}

export function getCircleOwnerApplication() {
  return request({
    url: '/api/v1/user/me/circle-owner-application',
    method: 'GET'
  })
}

export function applyForCircleOwner(payload) {
  return request({
    url: '/api/v1/user/me/circle-owner-application',
    method: 'POST',
    data: payload || {}
  })
}

export function getUserProfileById(targetUserId) {
  const safeId = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/user/profiles/${safeId}`,
    method: 'GET'
  })
}

export function getUserProfileMiniappCode(targetUserId) {
  const safeId = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/user/profiles/${safeId}/miniapp-code`,
    method: 'GET'
  })
}

export function unlockUserProfileContact(targetUserId) {
  const safeId = encodeURIComponent(String(targetUserId || '').trim())
  return request({
    url: `/api/v1/user/profiles/${safeId}/contact-unlock`,
    method: 'POST'
  })
}

export function updateCurrentUserProfile(payload) {
  return request({
    url: '/api/v1/user/me',
    method: 'PATCH',
    data: payload || {}
  })
}

export function createContentReport(payload = {}) {
  return request({
    url: '/api/v1/product-safety/reports',
    method: 'POST',
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

export function getMyFollowingList(params = {}) {
  const query = []
  const offset = Number(params.offset || 0)
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)

  if (offset > 0) {
    query.push(`offset=${offset}`)
  }
  query.push(`limit=${limit}`)

  const queryString = query.length > 0 ? `?${query.join('&')}` : ''
  return request({
    url: `/api/v1/user/me/following${queryString}`,
    method: 'GET'
  })
}

export function getMyFollowersList(params = {}) {
  const query = []
  const offset = Number(params.offset || 0)
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)

  if (offset > 0) {
    query.push(`offset=${offset}`)
  }
  query.push(`limit=${limit}`)

  const queryString = query.length > 0 ? `?${query.join('&')}` : ''
  return request({
    url: `/api/v1/user/me/followers${queryString}`,
    method: 'GET'
  })
}
