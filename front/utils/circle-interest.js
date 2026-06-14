const CIRCLE_INTEREST_EVENT = 'circle-interest-changed'
const CIRCLE_INTEREST_STORAGE_KEY = 'circle_interest_state_v1'

const normalizeCircleCode = (value) => String(value || '').trim()

export function publishCircleInterestChange(circleCode, interested) {
  const normalizedCode = normalizeCircleCode(circleCode)
  if (!normalizedCode) {
    return
  }

  const payload = {
    circleCode: normalizedCode,
    interested: Boolean(interested),
    updatedAt: Date.now()
  }

  uni.setStorageSync(CIRCLE_INTEREST_STORAGE_KEY, payload)
  if (typeof uni.$emit === 'function') {
    uni.$emit(CIRCLE_INTEREST_EVENT, payload)
  }
}

export function consumeLatestCircleInterestChange() {
  const payload = uni.getStorageSync(CIRCLE_INTEREST_STORAGE_KEY)
  if (!payload || typeof payload !== 'object') {
    return null
  }

  const circleCode = normalizeCircleCode(payload.circleCode)
  if (!circleCode) {
    return null
  }

  uni.removeStorageSync(CIRCLE_INTEREST_STORAGE_KEY)
  return {
    circleCode,
    interested: Boolean(payload.interested),
    updatedAt: Number(payload.updatedAt || 0)
  }
}

export function subscribeCircleInterestChange(handler) {
  if (typeof uni.$on === 'function') {
    uni.$on(CIRCLE_INTEREST_EVENT, handler)
  }
}

export function unsubscribeCircleInterestChange(handler) {
  if (typeof uni.$off === 'function') {
    uni.$off(CIRCLE_INTEREST_EVENT, handler)
  }
}
