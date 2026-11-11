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

export function getPointsCenterOverview() {
  return request({
    url: '/api/v1/points/center',
    method: 'GET'
  })
}

export function getPointsRecords(params = {}) {
  const query = buildQuery({
    cursor: String(params.cursor || '').trim(),
    limit: Math.min(Math.max(Number(params.limit || 20), 1), 50)
  })
  return request({
    url: `/api/v1/points/records${query ? `?${query}` : ''}`,
    method: 'GET'
  })
}

export function claimPointsCheckIn() {
  return request({
    url: '/api/v1/points/check-in',
    method: 'POST'
  })
}
