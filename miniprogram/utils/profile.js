/**
 * 人脉卡 / 名片字段映射
 *
 * 原生小程序没有 computed，所有展示用的派生字段（认证标识、头像兜底、
 * 标签清洗、行业兜底文案）必须在 setData 之前一次性算好。
 * 这里把 uni 版散落在页面里的映射逻辑收敛成纯函数，列表页与详情页共用。
 */

import { getApiBaseUrl } from './request'

export const DEFAULT_AVATAR_URL = 'https://cos.cnptec.site/static/logo.png'
export const BADGE_CERTIFICATION = 'https://cos.cnptec.site/static/icon/certification.png'
export const BADGE_MEMBER = 'https://cos.cnptec.site/static/icon/mennber1.png'
export const BADGE_CIRCLE_OWNER = 'https://cos.cnptec.site/static/icon/leader.png?v=20260623'

const MEMBER_ACTIVE_STATUS = new Set([
  'active', 'opened', 'member', 'vip', 'paid', 'enabled', 'on'
])

export function isTruthyValue(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value === 1
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    return ['1', 'true', 'yes', 'active', 'opened', 'enabled', 'on'].indexOf(normalized) >= 0
  }
  return false
}

export function resolveAvatarUrl(url) {
  const normalized = String(url || '').trim()
  const lower = normalized.toLowerCase()
  if (!normalized || ['null', 'undefined', 'none'].indexOf(lower) >= 0) {
    return DEFAULT_AVATAR_URL
  }
  if (lower.indexOf('/static/logo.png') >= 0) {
    return DEFAULT_AVATAR_URL
  }
  if (/^https?:\/\//.test(normalized)) {
    return normalized
  }
  if (normalized.indexOf('/') === 0) {
    const base = String(getApiBaseUrl() || 'https://www.cnptec.site').trim()
    return `${base}${normalized}`
  }
  return normalized
}

export function resolveMemberEnabled(profile = {}) {
  const candidateFlags = [
    profile.is_member,
    profile.member_opened,
    profile.pro_member,
    profile.vip_opened,
    profile.vip_member
  ]

  if (candidateFlags.some((flag) => isTruthyValue(flag))) {
    return true
  }

  const statusText = String(profile.member_status || profile.vip_status || '').trim().toLowerCase()
  return MEMBER_ACTIVE_STATUS.has(statusText)
}

export function resolveIdentityVerified(profile = {}) {
  return isTruthyValue(profile.is_verified)
    || isTruthyValue(profile.real_name_verified)
    || Boolean(String(profile.verified_real_name || '').trim())
}

export function resolveCircleOwnerEnabled(profile = {}) {
  return isTruthyValue(profile.is_circle_owner)
    || isTruthyValue(profile.circle_owner)
    || isTruthyValue(profile.owner_certified)
    || isTruthyValue(profile.circle_owner_status)
}

/** 过滤后端偶发返回的乱码标签（??? 或问号占比过半） */
export function isCorruptedTag(text) {
  const value = String(text || '').trim()
  if (!value) return true
  if (value.indexOf('???') >= 0) return true
  const questionCount = (value.match(/[?]/g) || []).length
  return questionCount >= 2 && questionCount >= Math.max(Math.floor(value.length / 2), 1)
}

export function normalizeTag(text) {
  const value = String(text || '').trim()
  if (isCorruptedTag(value)) return ''
  return value.replace(/[\s\u3000]+/g, ' ')
}

export function dedupeTags(items = []) {
  const seen = new Set()
  const result = []
  for (const raw of items || []) {
    const item = normalizeTag(raw)
    if (!item || seen.has(item)) continue
    seen.add(item)
    result.push(item)
  }
  return result
}

export function parseReasonDetail(value) {
  if (!value) return {}
  if (typeof value === 'object') return value
  if (typeof value !== 'string') return {}
  try {
    const parsed = JSON.parse(value)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (err) {
    return {}
  }
}

export function normalizeStringList(value) {
  if (Array.isArray(value)) return dedupeTags(value)
  if (typeof value === 'string') {
    return dedupeTags(value.split(/[，,、|]/).map((item) => item.trim()).filter(Boolean))
  }
  return []
}

export function normalizeCircleList(value) {
  if (Array.isArray(value)) return dedupeTags(value)
  if (typeof value === 'string') {
    return dedupeTags(
      value.replace(/\uFF0C/g, ',').replace(/\u3001/g, ',')
        .split(/[|,]/).map((item) => item.trim()).filter(Boolean)
    )
  }
  return []
}

/**
 * 把后端推荐流的一条记录映射成卡片视图模型
 * 列表页与详情页共用，保证两处字段口径一致
 */
export function mapMemberCard(item = {}, uiText = {}) {
  const businessUserId = String(item.user_id || item.userId || '').trim()
  const cityName = String(item.city_name || '').trim()
  const intro = String(item.intro || '').trim()
  const industryLabel = String(item.industry_label || '').trim()
  const reasonTags = Array.isArray(item.reason_tags)
    ? item.reason_tags.map((tag) => normalizeTag(tag)).filter(Boolean)
    : []
  const reasonDetail = parseReasonDetail(item.reason_detail)

  return {
    id: businessUserId || `${String(item.nickname || 'guest').trim()}-${cityName || 'city'}`,
    businessUserId,
    name: String(item.nickname || '').trim() || uiText.unnamedUser || '未命名用户',
    verifyType: resolveIdentityVerified(item) ? 'lv1' : '',
    verifyText: resolveIdentityVerified(item) ? (uiText.verifyLv1 || 'LV1 已认证') : '',
    detailLine: industryLabel || uiText.defaultRole || '暂未填写行业',
    cityName,
    distanceText: String(item.distance_text || '').trim(),
    memberEnabled: resolveMemberEnabled(item),
    circleOwner: resolveCircleOwnerEnabled(item),
    circleTags: intro ? [intro] : [],
    reasonTags,
    activeText: String(item.active_text || '').trim() || uiText.activeFallback || '最近活跃',
    avatar: resolveAvatarUrl(item.avatar_url || item.avatarUrl || item.avatar || item.headimgurl || item.wx_avatar_url),
    postCount: Number(item.post_count || item.postCount || 0),
    followed: Boolean(item.is_followed || item.followed || item.follow_status === 'followed'),
    score: Number(item.score || 0),
    reasonDetail
  }
}
