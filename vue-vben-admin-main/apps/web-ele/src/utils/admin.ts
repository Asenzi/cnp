export function formatDateTime(value: null | string | undefined) {
  if (!value) {
    return '--';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '--';
  }
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  const hour = `${date.getHours()}`.padStart(2, '0');
  const minute = `${date.getMinutes()}`.padStart(2, '0');
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

export function formatAmount(value: null | number | string | undefined) {
  const safeValue = Number(value || 0);
  if (!Number.isFinite(safeValue)) {
    return '0.00';
  }
  return safeValue.toFixed(2);
}

export function formatCompactNumber(value: null | number | string | undefined) {
  const safeValue = Number(value || 0);
  if (!Number.isFinite(safeValue)) {
    return '0';
  }
  if (safeValue >= 10000) {
    return `${(safeValue / 10000).toFixed(1)}w`;
  }
  return `${Math.round(safeValue)}`;
}

export function resolveStatusTagType(status: null | string | undefined) {
  if (
    status === 'active' ||
    status === 'approved' ||
    status === 'paid' ||
    status === 'auto_approved'
  ) {
    return 'success';
  }
  if (status === 'pending') {
    return 'warning';
  }
  if (
    status === 'inactive' ||
    status === 'offline' ||
    status === 'rejected' ||
    status === 'failed'
  ) {
    return 'danger';
  }
  return 'info';
}

export function formatPostMode(mode: null | string | undefined) {
  if (mode === 'cooperate') {
    return '找合作';
  }
  if (mode === 'resource') {
    return '找资源';
  }
  return mode || '--';
}

export function formatVerificationType(value: null | string | undefined) {
  if (value === 'real_name') {
    return '实名认证';
  }
  if (value === 'enterprise') {
    return '企业认证';
  }
  if (value === 'business_card') {
    return '名片认证';
  }
  return value || '--';
}

export function formatContentReviewType(value: null | string | undefined) {
  if (value === 'profile') {
    return '个人信息审核';
  }
  if (value === 'circle') {
    return '圈子信息审核';
  }
  if (value === 'post') {
    return '资源信息审核';
  }
  return value || '--';
}

export function formatReviewActionType(value: null | string | undefined) {
  if (value === 'create') {
    return '新建';
  }
  if (value === 'update') {
    return '修改';
  }
  return value || '--';
}

export function formatReviewTriggerReason(value: null | string | undefined) {
  if (value === 'monthly_limit') {
    return '超出当月免费修改次数';
  }
  if (value === 'risk_keywords') {
    return '命中系统风控词';
  }
  return value || '--';
}
