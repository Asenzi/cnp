import { request } from '../utils/request'

export function getNetworkRecommendations(params = {}) {
  const query = []
  const appendQuery = (key, value) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    query.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  }

  const tab = String(params.tab || 'recommend').trim()
  const requestId = String(params.request_id || '').trim()
  const cursor = String(params.cursor || '').trim()
  const keyword = String(params.keyword || '').trim()
  const cityName = String(params.city_name || '').trim()
  const industryLabel = String(params.industry_label || '').trim()
  const domain = String(params.domain || '').trim()
  const excludeUserIds = Array.isArray(params.exclude_user_ids)
    ? params.exclude_user_ids.map((id) => String(id || '').trim()).filter(Boolean).join(',')
    : String(params.exclude_user_ids || '').trim()
  const limit = Number(params.limit || 20)

  appendQuery('tab', tab)
  appendQuery('request_id', requestId)
  appendQuery('cursor', cursor)
  appendQuery('keyword', keyword)
  appendQuery('city_name', cityName)
  appendQuery('industry_label', industryLabel)
  appendQuery('domain', domain)
  appendQuery('exclude_user_ids', excludeUserIds)
  appendQuery('limit', Math.min(Math.max(limit, 1), 50))

  return request({
    url: `/api/v1/network/recommendations?${query.join('&')}`,
    method: 'GET'
  })
}

export function getNetworkFilterOptions() {
  return request({
    url: '/api/v1/network/filters',
    method: 'GET'
  })
}

export function reportNetworkImpressions(payload = {}) {
  return request({
    url: '/api/v1/network/impressions/batch',
    method: 'POST',
    data: {
      request_id: payload.request_id || '',
      scene: payload.scene || 'discover',
      tab: payload.tab || 'recommend',
      target_user_ids: Array.isArray(payload.target_user_ids) ? payload.target_user_ids : []
    }
  })
}

export function reportNetworkFeedback(payload = {}) {
  return request({
    url: '/api/v1/network/feedback',
    method: 'POST',
    data: {
      request_id: payload.request_id || '',
      scene: payload.scene || 'discover',
      tab: payload.tab || 'recommend',
      target_user_id: payload.target_user_id || '',
      event_type: payload.event_type || 'click_card',
      ext: payload.ext || {}
    }
  })
}
