import { emit } from './event-bus'

export const EVENT_USER_CHANGED = 'user:changed'
export const EVENT_UNREAD_CHANGED = 'unread:changed'

function getGlobalData() {
  const app = getApp()
  return app ? app.globalData : {}
}

export function getToken() {
  return getGlobalData().token || ''
}

export function isLoggedIn() {
  return Boolean(getToken())
}

export function getUserInfo() {
  return getGlobalData().userInfo || null
}

export function getUnreadCount() {
  return Number(getGlobalData().unreadCount) || 0
}

export function setUser(token, userInfo) {
  const app = getApp()
  if (!app) {
    return
  }

  app.setLoginState(token || '', userInfo || null)

  try {
    if (token) {
      wx.setStorageSync('token', token)
      wx.setStorageSync('userInfo', userInfo || null)
      wx.setStorageSync('isLoggedIn', true)
    }
  } catch (error) {
    // 忽略写入失败
  }

  emit(EVENT_USER_CHANGED, {
    isLoggedIn: Boolean(token),
    userInfo: userInfo || null
  })
}

export function clearUser() {
  const app = getApp()
  if (!app) {
    return
  }
  app.clearLoginState()
  emit(EVENT_USER_CHANGED, { isLoggedIn: false, userInfo: null })
}

export function setUnreadCount(count) {
  const app = getApp()
  if (!app) {
    return
  }
  const next = Math.max(Number(count) || 0, 0)
  if (app.globalData.unreadCount === next) {
    return
  }
  app.globalData.unreadCount = next
  emit(EVENT_UNREAD_CHANGED, next)
}

export function setCurrentCity(city) {
  const app = getApp()
  if (!app) {
    return
  }
  app.globalData.currentCity = city || ''
}
