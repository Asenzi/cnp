/**
 * 名片详情视图模型
 * 对应 uni 版 pages/me/card/modules/profile-home-view-model.js
 *
 * 详情页字段比列表页更复杂（徽章数组、统计卡、行业多值拆分），
 * 同样必须在 setData 之前算完。
 */

import { resolveAvatarUrl, isTruthyValue } from './profile'

const DEFAULT_AVATAR = 'https://cos.cnptec.site/static/logo.png'

const ACTIVE_TEXT_VALUES = new Set([
  '1', 'true', 'yes', 'y', 'active', 'opened', 'member', 'vip', 'paid',
  'enabled', 'on', 'approved', 'verified', '已开通', '会员', '已认证', '已实名', '圈主'
])

const IDENTITY_BADGE_ICONS = {
  certification: 'https://cos.cnptec.site/static/icon/certification.png',
  member: 'https://cos.cnptec.site/static/icon/mennber1.png',
  leader: 'https://cos.cnptec.site/static/icon/leader.png?v=20260623'
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed < 0) return fallback
  return parsed
}

export function formatCount(value, fallback = '0') {
  const n = toNumber(value, Number(fallback) || 0)
  return n.toLocaleString('zh-CN')
}

function isActiveValue(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value > 0
  const text = String(value === null || value === undefined ? '' : value).trim().toLowerCase()
  return Boolean(text && ACTIVE_TEXT_VALUES.has(text))
}

export function resolveIdentityBadges(profile = {}) {
  const badges = []
  if (isActiveValue(profile.is_verified) || isActiveValue(profile.real_name_verified)
    || isActiveValue(profile.verified) || String(profile.verified_real_name || '').trim()) {
    badges.push({ key: 'certification', icon: IDENTITY_BADGE_ICONS.certification, label: '实名' })
  }
  if (isActiveValue(profile.is_member) || isActiveValue(profile.member_opened)
    || isActiveValue(profile.vip_opened) || isActiveValue(profile.pro_member)) {
    badges.push({ key: 'member', icon: IDENTITY_BADGE_ICONS.member, label: '会员' })
  }
  if (isActiveValue(profile.is_circle_owner) || isActiveValue(profile.circle_owner)
    || isActiveValue(profile.owner_certified)) {
    badges.push({ key: 'leader', icon: IDENTITY_BADGE_ICONS.leader, label: '圈主' })
  }
  return badges
}

export function resolveMetaLine(profile = {}) {
  const industry = String(profile.industry_label || '').trim()
  const jobTitle = String(profile.job_title || profile.card_title || profile.position || profile.role || '').trim()
  const parts = [industry, jobTitle].filter(Boolean)
  return parts.length ? parts.join(' / ') : '暂未完善行业 / 职位'
}

export function resolveStats(profile = {}, options = {}) {
  const networkCount = toNumber(profile.network_count, toNumber(profile.follower_count, 0))
  const circleCount = toNumber(options.circleCount, toNumber(profile.circle_count, 0))
  const resourceCount = toNumber(options.resourceCount, toNumber(profile.post_count, 0))

  return [
    { key: 'network', label: '人脉', value: formatCount(networkCount) },
    { key: 'circles', label: '圈子', value: formatCount(circleCount) },
    { key: 'resources', label: '资源', value: formatCount(resourceCount) }
  ]
}

export function resolveProfileHomeData(profile = {}, options = {}) {
  const nickname = String(profile.nickname || '').trim()
  const intro = String(profile.intro || '').trim()
  const avatarUrl = String(profile.avatar_url || '').trim()
  const cities = Array.isArray(profile.circle_names) ? profile.circle_names : []
  const locationLine = String(options.locationLine || profile.city_name || '').trim()

  return {
    userId: String(profile.user_id || profile.userId || '').trim(),
    name: nickname || '未命名用户',
    metaLine: resolveMetaLine(profile),
    locationLine,
    badges: resolveIdentityBadges(profile),
    isVerified: resolveIdentityBadges(profile).some((item) => item.key === 'certification'),
    avatarUrl: avatarUrl ? resolveAvatarUrl(avatarUrl) : DEFAULT_AVATAR,
    bio: intro || '这个人很低调，暂时还没有填写个人简介。',
    followed: Boolean(profile.is_followed || profile.followed || profile.is_following),
    circles: cities.map((name, index) => ({
      id: `circle-${index}`,
      name: String(name || '').trim(),
      role: index === 0 ? '圈主' : '成员'
    })).filter((item) => item.name),
    stats: resolveStats(profile, {
      circleCount: (profile.circle_names || []).length,
      resourceCount: options.resourceCount
    })
  }
}
