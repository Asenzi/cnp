import { request } from '../utils/request'

export function sendSmsCode(phone) {
  return request({
    url: '/api/v1/auth/sms-code',
    method: 'POST',
    data: { phone }
  })
}

export function loginBySmsCode(phone, code, inviteCode) {
  return request({
    url: '/api/v1/auth/login',
    method: 'POST',
    data: {
      phone,
      code,
      invite_code: String(inviteCode || '').trim() || undefined
    }
  })
}

export function loginByPassword(phone, password, inviteCode) {
  return request({
    url: '/api/v1/auth/password-login',
    method: 'POST',
    data: {
      phone,
      password,
      invite_code: String(inviteCode || '').trim() || undefined
    }
  })
}

export function loginByWechatMiniapp(payload) {
  return request({
    url: '/api/v1/auth/wechat-miniapp-login',
    method: 'POST',
    data: {
      ...(payload || {}),
      invite_code: String(payload?.invite_code || '').trim() || undefined
    }
  })
}

export function getWechatBindStatus() {
  return request({
    url: '/api/v1/auth/wechat-bind-status',
    method: 'GET'
  })
}

export function bindWechatMiniapp(payload) {
  return request({
    url: '/api/v1/auth/wechat-bind',
    method: 'POST',
    data: payload
  })
}

export function sendPhoneBindCode(phone) {
  return request({
    url: '/api/v1/auth/phone-bind-code',
    method: 'POST',
    data: { phone }
  })
}

export function bindPhone(phone, code) {
  return request({
    url: '/api/v1/auth/phone-bind',
    method: 'POST',
    data: { phone, code }
  })
}

export function sendPasswordChangeCode() {
  return request({
    url: '/api/v1/auth/password-change-code',
    method: 'POST',
    data: {}
  })
}

export function changePasswordBySms(code, newPassword) {
  return request({
    url: '/api/v1/auth/password-change',
    method: 'POST',
    data: { code, new_password: newPassword }
  })
}
