export const VERIFICATION_TYPE = {
  ENTERPRISE: 'enterprise',
  REAL_NAME: 'real_name',
  BUSINESS_CARD: 'business_card'
}

export const VERIFICATION_STATUS = {
  NOT_SUBMITTED: 'not_submitted',
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected'
}

export const verificationTypeList = [
  {
    type: VERIFICATION_TYPE.ENTERPRISE,
    title: '企业认证',
    desc: '验证企业身份，解锁发布职位等企业权益',
    icon: '/static/me-icons/corporate-primary.png'
  },
  {
    type: VERIFICATION_TYPE.REAL_NAME,
    title: '实名认证',
    desc: '核实真实身份，建立职场信任基石',
    icon: '/static/me-icons/badge-primary.png'
  }
]

const STATUS_TEXT_MAP = {
  [VERIFICATION_STATUS.NOT_SUBMITTED]: '未认证',
  [VERIFICATION_STATUS.PENDING]: '审核中',
  [VERIFICATION_STATUS.APPROVED]: '已通过',
  [VERIFICATION_STATUS.REJECTED]: '已驳回'
}

const ACTION_TEXT_MAP = {
  [VERIFICATION_STATUS.NOT_SUBMITTED]: '去认证',
  [VERIFICATION_STATUS.PENDING]: '审核中',
  [VERIFICATION_STATUS.APPROVED]: '已通过',
  [VERIFICATION_STATUS.REJECTED]: '重新认证'
}

export function getStatusText(status) {
  return STATUS_TEXT_MAP[status] || STATUS_TEXT_MAP[VERIFICATION_STATUS.NOT_SUBMITTED]
}

export function getActionText(status) {
  return ACTION_TEXT_MAP[status] || ACTION_TEXT_MAP[VERIFICATION_STATUS.NOT_SUBMITTED]
}

export function isActionDisabled(status) {
  return status === VERIFICATION_STATUS.PENDING || status === VERIFICATION_STATUS.APPROVED
}

export function normalizeOverviewItems(items) {
  const normalizedMap = {}

  if (Array.isArray(items)) {
    items.forEach((item) => {
      if (!item || typeof item !== 'object') {
        return
      }
      const type = String(item.type || '').trim()
      if (!type) {
        return
      }
      normalizedMap[type] = {
        type,
        status: String(item.status || VERIFICATION_STATUS.NOT_SUBMITTED),
        reject_reason: item.reject_reason || '',
        submitted_at: item.submitted_at || '',
        reviewed_at: item.reviewed_at || ''
      }
    })
  }

  verificationTypeList.forEach((meta) => {
    if (!normalizedMap[meta.type]) {
      normalizedMap[meta.type] = {
        type: meta.type,
        status: VERIFICATION_STATUS.NOT_SUBMITTED,
        reject_reason: '',
        submitted_at: '',
        reviewed_at: ''
      }
    }
  })

  return normalizedMap
}
