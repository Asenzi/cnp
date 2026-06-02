import { request } from '../utils/request'

// 获取系统通知列表
export function getSystemNotifications(params = {}) {
  const offset = Math.max(Number(params.offset || 0), 0)
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)
  const query = [`offset=${offset}`, `limit=${limit}`]
  return request({
    url: `/api/v1/notifications/system?${query.join('&')}`,
    method: 'GET'
  })
}

// 标记通知为已读
export function markNotificationAsRead(notificationId) {
  const safeId = encodeURIComponent(String(notificationId || '').trim())
  return request({
    url: `/api/v1/notifications/${safeId}/read`,
    method: 'POST'
  })
}

// 获取未读通知数量
export function getUnreadNotificationCount() {
  return request({
    url: '/api/v1/notifications/unread-count',
    method: 'GET'
  })
}
