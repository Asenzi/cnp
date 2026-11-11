import { request } from '../utils/request'

export function getIncomeOverview(params = {}) {
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)
  const type = String(params.type || '').trim()
  const query = [`limit=${encodeURIComponent(String(limit))}`]
  if (type) query.push(`type=${encodeURIComponent(type)}`)
  if (params.beforeId) query.push(`before_id=${encodeURIComponent(String(params.beforeId))}`)
  return request({
    url: `/api/v1/settlement/income?${query.join('&')}`,
    method: 'GET'
  })
}

export function createWithdrawal(payload = {}) {
  return request({
    url: '/api/v1/settlement/withdrawals',
    method: 'POST',
    data: {
      amount: Number(payload.amount || 0),
      withdraw_type: String(payload.withdraw_type || 'wechat').trim() || 'wechat',
      withdraw_account: String(payload.withdraw_account || '').trim() || undefined
    }
  })
}

export function getWithdrawals(params = {}) {
  const limit = Math.min(Math.max(Number(params.limit || 30), 1), 100)
  const query = [`limit=${encodeURIComponent(String(limit))}`]
  if (params.beforeId) query.push(`before_id=${encodeURIComponent(String(params.beforeId))}`)
  if (params.status) query.push(`status=${encodeURIComponent(String(params.status))}`)
  return request({
    url: `/api/v1/settlement/withdrawals?${query.join('&')}`,
    method: 'GET'
  })
}
