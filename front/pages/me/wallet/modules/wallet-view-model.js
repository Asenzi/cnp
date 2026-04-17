const SUCCESS_STATUS_SET = new Set(['paid', 'success', 'succeeded', 'done'])
const PENDING_STATUS_SET = new Set(['pending', 'processing', 'created'])
const FAILED_STATUS_SET = new Set(['failed', 'closed', 'cancelled', 'canceled'])

const DEFAULT_SAMPLE_RECORDS = [
  {
    id: 'sample_income_1',
    title: '佣金收入',
    timeText: '今天, 14:20',
    amount: 2450,
    statusText: '交易成功',
    iconPath: '/static/me-icons/payments-green.png',
    iconBgClass: 'icon-bg-blue',
    sortTs: Date.now() - 1
  },
  {
    id: 'sample_expense_1',
    title: '会员费支出',
    timeText: '昨天',
    amount: -1200,
    statusText: '交易成功',
    iconPath: '/static/me-icons/description-primary.png',
    iconBgClass: 'icon-bg-orange',
    sortTs: Date.now() - 2
  }
]

function toNumber(value, fallback = 0) {
  const n = Number(value)
  if (!Number.isFinite(n)) {
    return fallback
  }
  return n
}

function toTimestamp(rawTime) {
  const text = String(rawTime || '').trim()
  if (!text) {
    return 0
  }
  const parsed = new Date(text.replace(' ', 'T'))
  const ts = parsed.getTime()
  if (!Number.isFinite(ts)) {
    return 0
  }
  return ts
}

export function formatMoney(amount, fractionDigits = 2) {
  const n = toNumber(amount, 0)
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  })
}

export function formatWalletBalance(amount) {
  return formatMoney(amount, 2)
}

function formatOrderTime(rawTime) {
  const text = String(rawTime || '').trim()
  if (!text) {
    return '--'
  }
  const date = new Date(text.replace(' ', 'T'))
  if (!Number.isFinite(date.getTime())) {
    return text
  }

  const now = new Date()
  const isSameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  if (isSameDay) {
    const hh = `${date.getHours()}`.padStart(2, '0')
    const mm = `${date.getMinutes()}`.padStart(2, '0')
    return `今天, ${hh}:${mm}`
  }

  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
}

function normalizeStatus(rawStatus) {
  const status = String(rawStatus || '').trim().toLowerCase()
  if (SUCCESS_STATUS_SET.has(status)) {
    return 'success'
  }
  if (PENDING_STATUS_SET.has(status)) {
    return 'pending'
  }
  if (FAILED_STATUS_SET.has(status)) {
    return 'failed'
  }
  return 'success'
}

function resolveStatusLabel(status) {
  if (status === 'pending') {
    return '处理中'
  }
  if (status === 'failed') {
    return '交易失败'
  }
  return '交易成功'
}

function resolvePayChannelIcon(channel) {
  if (channel === 'wallet') {
    return {
      iconPath: '/static/me-icons/description-primary.png',
      iconBgClass: 'icon-bg-orange'
    }
  }
  if (channel === 'wxpay') {
    return {
      iconPath: '/static/me-icons/payments-green.png',
      iconBgClass: 'icon-bg-blue'
    }
  }
  return {
    iconPath: '/static/me-icons/corporate-primary.png',
    iconBgClass: 'icon-bg-slate'
  }
}

export function mapMemberOrderRecord(item) {
  const status = normalizeStatus(item?.status)
  const amount = toNumber(item?.paid_amount, 0)
  const channel = String(item?.pay_channel || '').trim().toLowerCase()
  const { iconPath, iconBgClass } = resolvePayChannelIcon(channel)
  const planName = String(item?.plan_name || '').trim()

  return {
    id: `member_${String(item?.order_no || item?.id || Math.random())}`,
    title: planName ? `${planName}费支出` : '会员费支出',
    timeText: formatOrderTime(item?.paid_at || item?.created_at),
    amount: -Math.abs(amount),
    statusText: resolveStatusLabel(status),
    iconPath,
    iconBgClass,
    sortTs: toTimestamp(item?.paid_at || item?.created_at)
  }
}

export function mapRechargeOrderRecord(item) {
  const status = normalizeStatus(item?.status)
  const amount = toNumber(item?.amount, 0)
  const channel = String(item?.pay_channel || '').trim().toLowerCase()
  const { iconPath, iconBgClass } = resolvePayChannelIcon(channel)

  return {
    id: `recharge_${String(item?.order_no || item?.id || Math.random())}`,
    title: '钱包充值',
    timeText: formatOrderTime(item?.paid_at || item?.created_at),
    amount: Math.abs(amount),
    statusText: resolveStatusLabel(status),
    iconPath,
    iconBgClass,
    sortTs: toTimestamp(item?.paid_at || item?.created_at)
  }
}

export function mergeWalletRecords(memberRecords = [], rechargeRecords = []) {
  const merged = [...(Array.isArray(memberRecords) ? memberRecords : []), ...(Array.isArray(rechargeRecords) ? rechargeRecords : [])]
  return merged.sort((a, b) => {
    const diff = Number(b?.sortTs || 0) - Number(a?.sortTs || 0)
    if (diff !== 0) {
      return diff
    }
    return String(b?.id || '').localeCompare(String(a?.id || ''))
  })
}

export function withFallbackRecords(records) {
  if (Array.isArray(records) && records.length) {
    return records
  }
  return [...DEFAULT_SAMPLE_RECORDS]
}
