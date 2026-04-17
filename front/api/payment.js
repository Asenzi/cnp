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

export function getMemberCenterOverview() {
  return request({
    url: '/api/v1/payment/member/center',
    method: 'GET'
  })
}

export function subscribeMemberPlan(payload = {}) {
  return request({
    url: '/api/v1/payment/member/subscribe',
    method: 'POST',
    data: {
      plan_id: String(payload.plan_id || '').trim(),
      pay_channel: String(payload.pay_channel || '').trim() || undefined,
      use_points_discount: typeof payload.use_points_discount === 'boolean' ? payload.use_points_discount : undefined
    }
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

export function createWalletRecharge(payload = {}) {
  return request({
    url: '/api/v1/payment/wallet/recharge',
    method: 'POST',
    data: {
      amount: Number(payload.amount || 0),
      pay_channel: String(payload.pay_channel || '').trim() || undefined
    }
  })
}

export function confirmWalletRechargePayment(orderNo, payload = {}) {
  const safeOrderNo = encodeURIComponent(String(orderNo || '').trim())
  return request({
    url: `/api/v1/payment/wallet/recharge/${safeOrderNo}/confirm`,
    method: 'POST',
    data: {
      transaction_id: String(payload.transaction_id || '').trim() || undefined,
      ext: payload.ext && typeof payload.ext === 'object' ? payload.ext : undefined
    }
  })
}

export function getWalletRechargeStatus(orderNo) {
  const safeOrderNo = encodeURIComponent(String(orderNo || '').trim())
  return request({
    url: `/api/v1/payment/wallet/recharge/${safeOrderNo}`,
    method: 'GET'
  })
}

export function getWalletRechargeOrders(params = {}) {
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/payment/wallet/recharge/orders${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}
