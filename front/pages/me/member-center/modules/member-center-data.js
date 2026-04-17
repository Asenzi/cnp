export const DEFAULT_BENEFITS = [
  {
    key: 'badge',
    title: '专属身份标识',
    desc: '彰显商务独特身份',
    iconPath: '/static/me-icons/badge-blue.png'
  },
  {
    key: 'contact',
    title: '解锁联系方式',
    desc: '直接获取核心资源',
    iconPath: '/static/me-icons/contact-page-primary.png'
  },
  {
    key: 'circle_discount',
    title: '社群加入优惠',
    desc: '低成本高效入圈',
    iconPath: '/static/me-icons/corporate-primary.png'
  },
  {
    key: 'boost',
    title: '展示权重提升',
    desc: '曝光率大幅翻倍',
    iconPath: '/static/me-icons/payments-green.png'
  },
  {
    key: 'support',
    title: '优先技术支持',
    desc: '专属客服，极速响应您的需求',
    iconPath: '/static/me-icons/shield-person-primary.png',
    wide: true
  }
]

export const DEFAULT_PLANS = [
  {
    id: 'yearly',
    name: '年度会员',
    subtitle: '平均每天仅需 ¥0.54',
    price: 198,
    originalPrice: 348,
    recommended: true,
    badgeText: '超值推荐 BEST VALUE'
  },
  {
    id: 'quarterly',
    name: '季度会员',
    subtitle: '更灵活的商务选择',
    price: 79,
    originalPrice: 87,
    recommended: false
  },
  {
    id: 'monthly',
    name: '月度会员',
    subtitle: '抢先体验会员权益',
    price: 29,
    originalPrice: 0,
    recommended: false
  }
]

const ACTIVE_STATUS_SET = new Set(['active', 'opened', 'member', 'vip', 'paid'])

function isTruthyValue(value) {
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value === 1
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    return normalized === '1' || normalized === 'true' || normalized === 'yes' || normalized === 'active'
  }
  return false
}

function toAmount(value) {
  const amount = Number(value)
  if (!Number.isFinite(amount) || amount <= 0) {
    return 0
  }
  return Math.round(amount * 100) / 100
}

function formatDate(raw) {
  const text = String(raw || '').trim()
  if (!text) {
    return '--'
  }
  const date = new Date(text.replace(' ', 'T'))
  const ts = date.getTime()
  if (!Number.isFinite(ts)) {
    return '--'
  }
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function resolveMemberStatus(profile = {}) {
  const directFlags = [
    profile.is_member,
    profile.member_opened,
    profile.is_vip,
    profile.vip_opened,
    profile.premium,
    profile.pro_member
  ]
  let opened = directFlags.some((flag) => isTruthyValue(flag))

  if (!opened) {
    const statusText = String(profile.member_status || profile.vip_status || '').trim().toLowerCase()
    if (ACTIVE_STATUS_SET.has(statusText)) {
      opened = true
    }
  }

  const expireAtRaw = profile.member_expire_at || profile.vip_expire_at || ''
  const expireTs = expireAtRaw ? new Date(String(expireAtRaw).replace(' ', 'T')).getTime() : NaN
  if (!opened && Number.isFinite(expireTs) && expireTs > Date.now()) {
    opened = true
  }

  return {
    opened,
    statusText: opened ? '已开通' : '未开通',
    expireDateText: opened ? formatDate(expireAtRaw) : '--'
  }
}

export function resolveMemberPlans(rawPlans) {
  const source = Array.isArray(rawPlans) && rawPlans.length ? rawPlans : DEFAULT_PLANS
  const normalized = source
    .map((item, index) => {
      const id = String(item?.id || `plan_${index + 1}`).trim()
      const name = String(item?.name || '').trim()
      if (!id || !name) {
        return null
      }
      const price = toAmount(item?.price)
      return {
        id,
        name,
        subtitle: String(item?.subtitle || '').trim(),
        price,
        originalPrice: toAmount(item?.originalPrice),
        recommended: Boolean(item?.recommended),
        badgeText: String(item?.badgeText || '超值推荐 BEST VALUE').trim()
      }
    })
    .filter(Boolean)

  if (!normalized.length) {
    return [...DEFAULT_PLANS]
  }

  if (!normalized.some((item) => item.recommended)) {
    normalized[0].recommended = true
  }
  return normalized
}
