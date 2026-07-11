const DEFAULT_AVATAR =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuDqqbTCr_4-av06yTd1jMijurv9b-g48KLuF73y2a71WCiIQ0B6TT1Hh9LXTmaVIqiBSfatljYpn_0VHZgyadNC8BzoDa51D9jbu3WYh2HlN-w6eVuPWWfb9-kShGc-TsXM6HbxUxYhNutZT8w5plD2sykpc-O2V7sWKHHoOAoVKsSS8bdUgymAuRCbUvEblq5r16M9x9cVYUqdLNxVtc_h2E4Z1dLM55K3XHnmYC7OYA4QqBtjm7MeMgAaUFgNRGhTOOkbyxmH6pKF'

const FEED_AVATAR_STACK_COLORS = ['#e2e8f0', '#cbd5e1', '#94a3b8']
const ACTIVE_TEXT_VALUES = new Set(['1', 'true', 'yes', 'y', 'active', 'opened', 'member', 'vip', 'paid', 'enabled', 'on', 'approved', 'verified', '已开通', '会员', '已认证', '已实名', '圈主'])
const IDENTITY_BADGE_ICONS = {
  certification: 'https://cos.cnptec.site/static/icon/certification.png',
  member: 'https://cos.cnptec.site/static/icon/mennber1.png',
  leader: 'https://cos.cnptec.site/static/icon/leader.png?v=20260623'
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed < 0) {
    return fallback
  }
  return parsed
}

function formatCount(value, fallback = '0') {
  const n = toNumber(value, Number(fallback) || 0)
  return n.toLocaleString('zh-CN')
}

function isActiveValue(value) {
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value > 0
  }
  const text = String(value ?? '').trim().toLowerCase()
  return Boolean(text && ACTIVE_TEXT_VALUES.has(text))
}

function resolveMemberEnabled(profile = {}) {
  const candidateFlags = [
    profile?.is_member,
    profile?.member_opened,
    profile?.pro_member,
    profile?.vip_opened,
    profile?.vip_member
  ]

  if (candidateFlags.some(isActiveValue)) {
    return true
  }

  const statusText = String(profile?.member_status || profile?.vip_status || '').trim().toLowerCase()
  return ACTIVE_TEXT_VALUES.has(statusText)
}

function resolveVerified(profile = {}) {
  return Boolean(
    isActiveValue(profile?.is_verified) ||
    isActiveValue(profile?.real_name_verified) ||
    isActiveValue(profile?.verified) ||
    isActiveValue(profile?.verifyType) ||
    isActiveValue(profile?.verifyText) ||
    String(profile?.verified_real_name || '').trim()
  )
}

function resolveCircleOwner(profile = {}) {
  return Boolean(
    isActiveValue(profile?.is_circle_owner) ||
    isActiveValue(profile?.circle_owner) ||
    isActiveValue(profile?.is_owner) ||
    isActiveValue(profile?.circle_owner_status) ||
    isActiveValue(profile?.owner_status)
  )
}

function resolveIdentityBadges(profile = {}) {
  const badges = []
  if (resolveVerified(profile)) {
    badges.push({ key: 'certification', icon: IDENTITY_BADGE_ICONS.certification, label: '实名' })
  }
  if (resolveMemberEnabled(profile)) {
    badges.push({ key: 'member', icon: IDENTITY_BADGE_ICONS.member, label: '会员' })
  }
  if (resolveCircleOwner(profile)) {
    badges.push({ key: 'leader', icon: IDENTITY_BADGE_ICONS.leader, label: '圈主' })
  }
  return badges
}

function resolveMetaLine(profile = {}) {
  const industry = String(profile?.industry_label || '').trim()
  const jobTitle = String(profile?.job_title || profile?.card_title || profile?.position || '').trim()
  const parts = [industry, jobTitle].filter(Boolean)
  return parts.length ? parts.join(' / ') : '暂未完善行业 / 职位'
}

function resolveStats(profile, options = {}) {
  const networkCount = toNumber(profile?.network_count, 0)
  const circleCount = toNumber(options.circleCount, toNumber(profile?.circle_count, 0))
  const resourceCount = toNumber(options.resourceCount, 0)

  return [
    { key: 'network', label: '人脉', value: formatCount(networkCount, '0'), trend: '12%' },
    { key: 'circles', label: '圈子', value: formatCount(circleCount, '0'), trend: '2%' },
    { key: 'resources', label: '资源', value: formatCount(resourceCount, '0'), trend: '1%' }
  ]
}

function resolvePostType(mode) {
  const normalizedMode = String(mode || '').trim().toLowerCase()
  if (normalizedMode === 'resource') {
    return {
      type: 'offer',
      typeText: '供给'
    }
  }
  if (normalizedMode === 'venue') {
    return {
      type: 'venue',
      typeText: '活动'
    }
  }
  return {
    type: 'need',
    typeText: '需求'
  }
}

function resolveIndustryLabels(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return []
  }

  const parts = raw
    .split(/[\/|｜,，、;；]/)
    .map((item) => String(item || '').trim())
    .filter(Boolean)

  const uniqueParts = []
  parts.forEach((item) => {
    if (!uniqueParts.includes(item)) {
      uniqueParts.push(item)
    }
  })

  if (uniqueParts.length) {
    return uniqueParts.slice(0, 2)
  }

  return [raw].slice(0, 2)
}

export function mapProfilePostItem(post = {}) {
  const { type, typeText } = resolvePostType(post.mode)
  const images = Array.isArray(post.images)
    ? post.images.map((item) => String(item || '').trim()).filter(Boolean)
    : []
  const industryLabels = resolveIndustryLabels(post.industry_label)
  const isInterested = Boolean(post.is_collected ?? post.collected ?? post.is_interested ?? post.interested ?? post.liked)
  const collectCount = toNumber(post.collect_count ?? post.favorite_count ?? post.like_count, 0)

  return {
    id:
      String(post.post_code || '').trim() ||
      String(post.created_at || '').trim() ||
      `post-${Math.random().toString(16).slice(2, 8)}`,
    postCode: String(post.post_code || '').trim(),
    type,
    typeText,
    timeText: String(post.time_text || '').trim() || '刚刚',
    title: String(post.title || '').trim() || '未命名资源',
    content: String(post.description || '').trim(),
    industryLabels,
    likes: collectCount,
    collectCount,
    favoriteCount: collectCount,
    comments: toNumber(post.comment_count, 0),
    readers: toNumber(post.view_count, 0),
    interested: isInterested,
    isInterested,
    is_interested: isInterested,
    collected: isInterested,
    is_collected: isInterested,
    liked: isInterested,
    avatars: images.length ? [] : [...FEED_AVATAR_STACK_COLORS],
    images
  }
}

export function mapProfileCircleItem(circle = {}) {
  return {
    id:
      String(circle.circle_code || '').trim() ||
      String(circle.name || '').trim() ||
      `circle-${Math.random().toString(16).slice(2, 8)}`,
    circleCode: String(circle.circle_code || '').trim(),
    name: String(circle.name || '').trim() || '未命名圈子',
    members: toNumber(circle.member_count, 0),
    role: circle.is_owner ? '圈主' : '成员',
    coverUrl: String(circle.avatar_url || circle.cover_url || '').trim(),
    industryLabel: String(circle.industry_label || '').trim()
  }
}

export function resolveProfileHomeData(profile = {}, options = {}) {
  const nickname = String(profile?.nickname || '').trim()
  const intro = String(profile?.intro || '').trim()
  const avatarUrl = String(profile?.avatar_url || '').trim()
  const isVerified = resolveVerified(profile)
  const posts = Array.isArray(options.posts) ? options.posts : []
  const circles = Array.isArray(options.circles) ? options.circles : []

  return {
    profile: {
      name: nickname || '未命名用户',
      metaLine: resolveMetaLine(profile),
      locationLine: String(options.locationLine || '').trim(),
      memberEnabled: resolveMemberEnabled(profile),
      badges: resolveIdentityBadges(profile),
      isVerified,
      avatarUrl: avatarUrl || DEFAULT_AVATAR,
      bio: intro || '这个人很低调，暂时还没有填写个人简介。'
    },
    stats: resolveStats(profile, {
      resourceCount: options.resourceCount ?? posts.length,
      circleCount: options.circleCount
    }),
    tabs: [
      { key: 'feed', label: '资源' },
      { key: 'circles', label: '圈子' }
    ],
    posts,
    circles
  }
}
