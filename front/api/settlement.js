import { request } from '../utils/request'

export function getIncomeOverview(params = {}) {
  const limit = Math.min(Math.max(Number(params.limit || 20), 1), 50)
  return request({
    url: `/api/v1/settlement/income?limit=${encodeURIComponent(String(limit))}`,
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
  return request({
    url: `/api/v1/settlement/withdrawals?limit=${encodeURIComponent(String(limit))}`,
    method: 'GET'
  })
}
