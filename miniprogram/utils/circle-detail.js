/**
 * 圈子详情页的展示字段映射
 * 对应 uni 版 pages/circles/detail/index.vue 里的
 * applyServerDetail / formatCountText / mapJoinTypeTag / sanitizeCircleImage
 */

const DEFAULT_LOGO = 'https://cos.cnptec.site/static/logo.png'
const LOCAL_FILE_PATTERN = /^(https?:\/\/tmp\/|wxfile:\/\/|file:\/\/|blob:|data:image\/)/i

/** 详情页里图片缺失时回退到默认 logo（与列表页不同，列表页直接留空走占位块） */
export function sanitizeCircleImage(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return DEFAULT_LOGO
  }
  if (LOCAL_FILE_PATTERN.test(normalized)) {
    return DEFAULT_LOGO
  }
  return normalized
}

export function formatCountText(value) {
  const count = Number(value || 0)
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}w`
  }
  return `${Math.max(0, Math.floor(count))}`
}

/** 加入机制 -> 展示标签 */
export function mapJoinTypeTag(joinType, joinPrice = 0) {
  if (joinType === 'paid' && Number(joinPrice || 0) > 0) {
    return '付费圈'
  }
  if (joinType === 'review') {
    return '审核制'
  }
  return '免费圈'
}

export function resolveCircleInterest(item = {}) {
  const value = item.is_collected ?? item.collected ?? item.is_interested ?? item.interested
  return Boolean(value)
}

const EMPTY_DETAIL = {
  circleCode: '',
  bannerImage: '',
  logoImage: DEFAULT_LOGO,
  title: '圈子详情',
  levelTag: '免费圈',
  membersText: '0 位成员',
  postsText: '0 条动态',
  description: '',
  notice: '',
  owner: {
    userId: '',
    name: '',
    role: '圈主',
    intro: '',
    avatar: DEFAULT_LOGO
  },
  priceNumber: 0,
  priceText: '0.00',
  collectCount: 0,
  isInterested: false,
  isJoined: false,
  joinRequestStatus: '',
  joinPaymentStatus: ''
}

/** 把后端详情接口的数据合并成页面直接可渲染的视图模型 */
export function buildCircleDetail(serverDetail = {}, prev = EMPTY_DETAIL) {
  const safe = serverDetail || {}
  const priceNumber = Number(safe.join_price || 0)
  const owner = safe.owner || {}

  return {
    circleCode: String(safe.circle_code || prev.circleCode || '').trim(),
    bannerImage: String(safe.cover_url || '').trim()
      ? sanitizeCircleImage(safe.cover_url)
      : String(prev.bannerImage || '').trim(),
    logoImage: sanitizeCircleImage(safe.avatar_url || safe.cover_url || prev.logoImage),
    title: String(safe.name || '').trim() || prev.title || EMPTY_DETAIL.title,
    levelTag: mapJoinTypeTag(String(safe.join_type || '').trim(), priceNumber),
    membersText: `${formatCountText(safe.member_count)} 位成员`,
    postsText: `${formatCountText(safe.post_count)} 条动态`,
    description: String(safe.description || '').trim() || prev.description || '',
    notice: String(safe.notice || safe.announcement || '').trim() || prev.notice || '',
    owner: {
      userId: String(owner.user_id || prev.owner?.userId || '').trim(),
      name: String(owner.nickname || '').trim() || prev.owner?.name || '',
      role: '圈主',
      intro: String(owner.intro || owner.title || '').trim() || prev.owner?.intro || '',
      avatar: sanitizeCircleImage(owner.avatar_url || prev.owner?.avatar)
    },
    priceNumber,
    priceText: priceNumber > 0 ? priceNumber.toFixed(2) : '0.00',
    collectCount: Number(safe.collect_count ?? safe.favorite_count ?? prev.collectCount ?? 0),
    isInterested: resolveCircleInterest(safe),
    isJoined: Boolean(safe.is_joined),
    joinRequestStatus: String(safe.join_request_status || '').trim(),
    joinPaymentStatus: String(safe.join_payment_status || '').trim()
  }
}

export function emptyCircleDetail() {
  return Object.assign({}, EMPTY_DETAIL, { owner: Object.assign({}, EMPTY_DETAIL.owner) })
}

/**
 * 底部"申请加入"按钮的文案与禁用态
 * 对应 uni 版的 joinActionText / joinActionDisabled
 */
export function mapJoinAction(status = '', paymentStatus = '', submitting = false) {
  const requestStatus = String(status || '').trim()
  const payStatus = String(paymentStatus || '').trim()

  if (submitting) {
    return { text: '处理中...', disabled: true }
  }
  if (requestStatus === 'pending' && payStatus === 'paid') {
    return { text: '等待圈主处理', disabled: true }
  }
  if (requestStatus === 'approved') {
    return { text: '已加入', disabled: true }
  }
  if (requestStatus === 'rejected') {
    return { text: '重新申请', disabled: false }
  }
  return { text: '申请加入', disabled: false }
}

/** 圈子成员列表项 */
export function mapCircleMember(member = {}, index = 0) {
  const safe = member || {}
  const userId = String(safe.user_id || safe.userId || '').trim()
  const industryLabel = String(safe.industry_label || '').trim()
  const cityName = String(safe.city_name || '').trim()

  return {
    id: userId || `member-${index}`,
    userId,
    name: String(safe.nickname || safe.name || '').trim() || '未命名成员',
    avatar: String(safe.avatar_url || '').trim(),
    intro: String(safe.intro || safe.title || '').trim(),
    industryLabel,
    cityName,
    metaText: [industryLabel, cityName].filter(Boolean).join(' · '),
    verified: Boolean(safe.is_verified),
    isOwner: Boolean(safe.is_owner || safe.role === 'owner')
  }
}
