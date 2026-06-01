import { getApiBaseUrl, request } from '../utils/request'

export function submitHelpFeedback(payload = {}) {
  return request({
    url: '/api/v1/feedback',
    method: 'POST',
    data: {
      feedback_type: String(payload.feedback_type || '').trim(),
      description: String(payload.description || '').trim(),
      contact: String(payload.contact || '').trim(),
      images: Array.isArray(payload.images) ? payload.images : [],
      source_page: String(payload.source_page || 'pages/me/help-feedback/index').trim(),
    }
  })
}

export function uploadHelpFeedbackImage(filePath, fileName = 'feedback-image') {
  const token = uni.getStorageSync('token')
  const header = token
    ? { Authorization: `Bearer ${token}` }
    : {}

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getApiBaseUrl()}/api/v1/feedback/assets/upload`,
      filePath: String(filePath || '').trim(),
      name: 'file',
      fileName: String(fileName || 'feedback-image').trim() || 'feedback-image',
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
          payload,
        })
      },
      fail: (err) => {
        reject({
          statusCode: 0,
          code: -1,
          message: err?.errMsg || 'Network error',
          payload: err,
        })
      }
    })
  })
}
