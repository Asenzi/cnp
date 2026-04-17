import { getApiBaseUrl, request } from '../utils/request'

const SUBMIT_URL_MAP = {
  real_name: '/api/v1/verification/real-name/submit',
  enterprise: '/api/v1/verification/enterprise/submit',
  business_card: '/api/v1/verification/business-card/submit'
}

export function getMyVerificationOverview() {
  return request({
    url: '/api/v1/verification/me',
    method: 'GET'
  })
}

export function getRealNameVerificationDetail() {
  return request({
    url: '/api/v1/verification/real-name/detail',
    method: 'GET'
  })
}

function submitVerificationByType(type, payload) {
  const url = SUBMIT_URL_MAP[type]
  if (!url) {
    return Promise.reject(new Error('Unsupported verification type'))
  }
  return request({
    url,
    method: 'POST',
    data: payload || {}
  })
}

export function submitRealNameVerification(payload) {
  return submitVerificationByType('real_name', payload)
}

export function startTencentRealNameVerification(payload) {
  return request({
    url: '/api/v1/verification/real-name/tencent/start',
    method: 'POST',
    data: payload || {}
  })
}

export function finishTencentRealNameVerification(payload) {
  return request({
    url: '/api/v1/verification/real-name/tencent/finish',
    method: 'POST',
    data: payload || {}
  })
}

export function submitEnterpriseVerification(payload) {
  return submitVerificationByType('enterprise', payload)
}

export function submitBusinessCardVerification(payload) {
  return submitVerificationByType('business_card', payload)
}

function uploadVerificationFile(url, filePath, fileName = '认证文件') {
  const token = uni.getStorageSync('token')
  const headers = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
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

export function uploadEnterpriseLicense(filePath, fileName = '营业执照') {
  return uploadVerificationFile(
    `${getApiBaseUrl()}/api/v1/verification/enterprise/license-file`,
    filePath,
    fileName
  )
}

export function uploadRealNameIdCard(filePath, side, fileName = '身份证照片') {
  const safeSide = side === 'back' ? 'back' : 'front'
  return uploadVerificationFile(
    `${getApiBaseUrl()}/api/v1/verification/real-name/id-card-file?side=${safeSide}`,
    filePath,
    fileName
  )
}
