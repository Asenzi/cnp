/**
 * 资源 / 动态卡片字段映射
 *
 * 对应 uni 版 pages/me/card/modules/profile-home-view-model.js 的
 * mapProfilePostItem。原生没有 computed，列表项的展示字段必须
 * 在 setData 之前一次性算好（派生字段预计算，见 NATIVE_MP_PATTERNS.md）。
 */

const FEED_AVATAR_STACK_COLORS = ['#e2e8f0', '#cbd5e1', '#94a3b8']

function toNumber(value, fallback = 0) {
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}

/** 供给 / 需求 / 活动 三种类型徽标 */
function resolvePostType(mode) {
  const normalizedMode = String(mode || '').trim().toLowerCase()
  if (normalizedMode === 'resource') {
    return { type: 'offer', typeText: '供给' }
  }
  if (normalizedMode === 'venue') {
    return { type: 'venue', typeText: '活动' }
  }
  return { type: 'need', typeText: '需求' }
}

/** 行业标签按分隔符拆开，最多取 2 个 */
function resolveIndustryLabels(value) {
  const raw = String(value || '').trim()
  if (!raw) return []

  const parts = raw
    .split(/[\/|｜,，、;；]/)
    .map((item) => String(item || '').trim())
    .filter(Boolean)

  const uniqueParts = []
  parts.forEach((item) => {
    if (!uniqueParts.includes(item)) uniqueParts.push(item)
  })

  if (uniqueParts.length) return uniqueParts.slice(0, 2)
  return [raw].slice(0, 2)
}

/**
 * @param {Object} post 后端返回的原始资源项
 * @returns {Object} 视图模型，字段名与 wxml 一一对应
 */
export function mapResourcePostItem(post = {}) {
  const { type, typeText } = resolvePostType(post.mode)
  const images = Array.isArray(post.images)
    ? post.images.map((item) => String(item || '').trim()).filter(Boolean)
    : []
  const industryLabels = resolveIndustryLabels(post.industry_label)
  const isInterested = Boolean(
    post.is_collected ?? post.collected ?? post.is_interested ?? post.interested ?? post.liked
  )
  const collectCount = toNumber(
    post.collect_count ?? post.favorite_count ?? post.like_count,
    0
  )

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

/** 阅读数 / 收藏数的展示文案收敛到一个地方，避免每个页面各写一遍 */
export function resolveResourceStats(item = {}) {
  const readers = toNumber(item.readers, 0)
  const collect = toNumber(item.collectCount, 0)
  return {
    readersText: `${readers} 阅读`,
    collectText: `${collect} 收藏`
  }
}
