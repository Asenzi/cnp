/**
 * 圈子列表卡片的展示字段映射
 *
 * 对应 uni 版 pages/tab/circles/index.vue 里的
 * mapCircleCard / formatCompactNumber / sanitizeCircleImage。
 *
 * 原生没有 computed，所有展示字段必须在 setData 之前一次性算好，
 * 因此统一收在这里，页面只负责调用。
 */

const UNNAMED_CIRCLE = '未命名圈子'
const DEFAULT_DESC = '欢迎进入圈子详情了解更多'

/** 后端头像里常见的一张默认 logo，列表里应当当作"没有封面"处理 */
const PLACEHOLDER_LOGO = 'https://cos.cnptec.site/static/logo.png'
const PLACEHOLDER_LOGO_PATTERN = /\/static\/logo\.png(?:[?#].*)?$/i
/** 本地临时文件路径在列表里无法展示 */
const LOCAL_FILE_PATTERN = /^(https?:\/\/tmp\/|wxfile:\/\/|file:\/\/|blob:|data:image\/)/i

/** 12345 -> 1.2w，1234 -> 1.2k */
export function formatCompactNumber(value) {
  const numeric = Math.max(Number(value || 0), 0)
  if (numeric >= 10000) {
    const wan = numeric / 10000
    return wan >= 10 ? `${Math.floor(wan)}w` : `${wan.toFixed(1)}w`
  }
  if (numeric >= 1000) {
    const k = numeric / 1000
    return k >= 10 ? `${Math.floor(k)}k` : `${k.toFixed(1)}k`
  }
  return `${Math.floor(numeric)}`
}

/** 过滤掉默认 logo 与本地临时路径，返回可直接给 image 的 src */
export function sanitizeCircleImage(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }
  if (normalized === PLACEHOLDER_LOGO || PLACEHOLDER_LOGO_PATTERN.test(normalized)) {
    return ''
  }
  if (LOCAL_FILE_PATTERN.test(normalized)) {
    return ''
  }
  return normalized
}

/**
 * 收藏/感兴趣状态在后端各接口里字段名不统一，
 * 这里统一识别（与原版 mapCircleCard 的兼容逻辑一致）。
 */
export function resolveCircleInterest(item = {}) {
  return Boolean(
    item.is_collected
    || item.collected
    || item.is_interested
    || item.interested
    || item.followed
    || item.isFollowed
    || item.is_followed
  )
}

export function mapCircleCard(item = {}, index = 0) {
  const safeItem = item || {}
  const circleCode = String(safeItem.circle_code || '').trim()
  const description = String(safeItem.description || '').trim()
  const coverUrl = sanitizeCircleImage(safeItem.avatar_url || safeItem.cover_url || '')

  return {
    // wx:key 依赖 id，后端没给 circle_code 时兜底一个稳定的索引 id
    id: circleCode || `circle-${index}`,
    circleCode,
    title: String(safeItem.name || '').trim() || UNNAMED_CIRCLE,
    description: description || DEFAULT_DESC,
    industryLabel: String(safeItem.industry_label || '').trim(),
    ownerCity: String(safeItem.owner_city_name || '').trim(),
    members: formatCompactNumber(safeItem.member_count || 0),
    posts: formatCompactNumber(safeItem.post_count || 0),
    coverImage: coverUrl,
    ownerName: String(safeItem.owner_nickname || '').trim(),
    ownerAvatar: String(safeItem.owner_avatar_url || '').trim(),
    ownerVerified: Boolean(safeItem.owner_is_verified),
    collectCount: Number(safeItem.collect_count ?? safeItem.favorite_count ?? 0),
    interested: resolveCircleInterest(safeItem)
  }
}

/** 收藏状态变更后，就地改列表里的那一条（不重新请求整页） */
export function applyInterestToCard(card, interested) {
  if (!card) {
    return card
  }
  return Object.assign({}, card, { interested: Boolean(interested) })
}
