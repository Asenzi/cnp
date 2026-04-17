const DEFAULT_AVATAR =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuDqqbTCr_4-av06yTd1jMijurv9b-g48KLuF73y2a71WCiIQ0B6TT1Hh9LXTmaVIqiBSfatljYpn_0VHZgyadNC8BzoDa51D9jbu3WYh2HlN-w6eVuPWWfb9-kShGc-TsXM6HbxUxYhNutZT8w5plD2sykpc-O2V7sWKHHoOAoVKsSS8bdUgymAuRCbUvEblq5r16M9x9cVYUqdLNxVtc_h2E4Z1dLM55K3XHnmYC7OYA4QqBtjm7MeMgAaUFgNRGhTOOkbyxmH6pKF'

const FEED_AVATAR_STACK_COLORS = ['#e2e8f0', '#cbd5e1', '#94a3b8']
const MEMBER_ACTIVE_STATUS = new Set(['active', 'opened', 'member', 'vip', 'paid', 'enabled', 'on'])

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

function resolveMemberEnabled(profile = {}) {
  const candidateFlags = [
    profile?.is_member,
    profile?.member_opened,
    profile?.pro_member,
    profile?.vip_opened,
    profile?.vip_member
  ]

  if (candidateFlags.some(Boolean)) {
    return true
  }

  const statusText = String(profile?.member_status || profile?.vip_status || '').trim().toLowerCase()
  return MEMBER_ACTIVE_STATUS.has(statusText)
}

function resolveMetaLine(profile = {}) {
  const industry = String(profile?.industry_label || '').trim()
  const company = String(profile?.company_name || profile?.company || '').trim()
  const jobTitle = String(profile?.job_title || profile?.card_title || profile?.position || '').trim()
  const parts = [industry, company, jobTitle].filter(Boolean)

  return parts.length
    ? parts.join(' | ')
    : '暂未完善行业 | 公司 | 职位'
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
      typeText: '场地'
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
    likes: toNumber(post.like_count, 0),
    comments: toNumber(post.comment_count, 0),
    readers: toNumber(post.view_count, 0),
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
  const isVerified = Boolean(profile?.is_verified)
  const posts = Array.isArray(options.posts) ? options.posts : []
  const circles = Array.isArray(options.circles) ? options.circles : []

  return {
    profile: {
      name: nickname || '未命名用户',
      metaLine: resolveMetaLine(profile),
      memberEnabled: resolveMemberEnabled(profile),
      verifiedText: isVerified ? '已实名' : '未实名',
      isVerified,
      avatarUrl: avatarUrl || DEFAULT_AVATAR,
      bio: intro || '这个人很低调，暂时还没有填写个人简介。'
    },
    stats: resolveStats(profile, {
      resourceCount: options.resourceCount ?? posts.length,
      circleCount: options.circleCount
    }),
    tabs: [
      { key: 'feed', label: '动态 / 资源' },
      { key: 'circles', label: '加入的圈子' }
    ],
    posts,
    circles
  }
}
