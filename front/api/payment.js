import { request } from '../utils/request'

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

function getClientPlatform() {
  try {
    return String(uni.getSystemInfoSync()?.platform || '').trim().toLowerCase() || 'unknown'
  } catch {
    return 'unknown'
  }
}

export function getMemberCenterOverview() {
  return request({
    url: '/api/v1/payment/member/center',
    method: 'GET'
  })
}

export function getCircleOwnerOverview() {
  return request({
    url: '/api/v1/payment/circle-owner/overview',
    method: 'GET'
  })
}

export function purchaseCircleOwner(payload = {}) {
  return request({
    url: '/api/v1/payment/circle-owner/purchase',
    method: 'POST',
    data: {
      pay_channel: String(payload.pay_channel || '').trim() || undefined,
      client_platform: String(payload.client_platform || '').trim() || getClientPlatform()
    }
  })
}

export function getPartnerOverview(partnerType) {
  const type = encodeURIComponent(String(partnerType || '').trim())
  return request({
    url: `/api/v1/payment/partner/${type}/overview`,
    method: 'GET'
  })
}

export function purchasePartner(partnerType, payload = {}) {
  const type = encodeURIComponent(String(partnerType || '').trim())
  return request({
    url: `/api/v1/payment/partner/${type}/purchase`,
    method: 'POST',
    data: {
      pay_channel: String(payload.pay_channel || '').trim() || undefined,
      client_platform: String(payload.client_platform || '').trim() || getClientPlatform()
    }
  })
}

export function subscribeMemberPlan(payload = {}) {
  const data = {
    plan_id: String(payload.plan_id || '').trim(),
    pay_channel: String(payload.pay_channel || '').trim() || undefined,
    use_points_discount: typeof payload.use_points_discount === 'boolean' ? payload.use_points_discount : undefined,
    client_platform: String(payload.client_platform || '').trim() || getClientPlatform()
  }
  if (typeof payload.referral_invite_code === 'string') {
    data.referral_invite_code = payload.referral_invite_code.trim().toUpperCase()
  }
  return request({
    url: '/api/v1/payment/member/subscribe',
    method: 'POST',
    data
  })
}

export function confirmMemberOrderPayment(orderNo, payload = {}) {
  const safeOrderNo = encodeURIComponent(String(orderNo || '').trim())
  return request({
    url: `/api/v1/payment/member/orders/${safeOrderNo}/confirm`,
    method: 'POST',
    data: {
      transaction_id: String(payload.transaction_id || '').trim() || undefined,
      ext: payload.ext && typeof payload.ext === 'object' ? payload.ext : undefined
    }
  })
}

export function reportMemberPaymentClientError(payload = {}) {
  return request({
    url: '/api/v1/payment/member/payment-client-error',
    method: 'POST',
    data: {
      order_no: String(payload.order_no || '').trim(),
      scene: String(payload.scene || '').trim() || undefined,
      err_msg: String(payload.err_msg || payload.errMsg || '').trim() || undefined,
      err_code: payload.err_code ?? payload.errCode,
      ext: payload.ext && typeof payload.ext === 'object' ? payload.ext : undefined
    }
  })
}

export function getMemberOrderStatus(orderNo) {
  const safeOrderNo = encodeURIComponent(String(orderNo || '').trim())
  return request({
    url: `/api/v1/payment/member/orders/${safeOrderNo}`,
    method: 'GET'
  })
}

export function getMemberOrders(params = {}) {
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/payment/member/orders${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}
