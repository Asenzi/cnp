const PARTNER_REFERRAL_TRACKED_KEY = 'partner_referral_tracked_v1'
const PARTNER_REFERRAL_CODE_KEY = 'partner_referral_code_v1'
const LOGIN_INVITE_CODE_KEY = '__INVITE_CODE__'


function readInviteCode(options = {}) {
  const query = options?.query || {}
  return String(query.inviteCode || query.invite_code || '').trim().toUpperCase()
}

export function capturePartnerReferralLaunch(options = {}) {
  const inviteCode = readInviteCode(options)
  if (inviteCode) {
    uni.setStorageSync(PARTNER_REFERRAL_TRACKED_KEY, true)
    uni.setStorageSync(PARTNER_REFERRAL_CODE_KEY, inviteCode)
    uni.setStorageSync(LOGIN_INVITE_CODE_KEY, inviteCode)
    return
  }

  // No invitation on this entry means platform, regardless of older visits.
  // Orders already submitted retain their server-side attribution snapshot.
  uni.setStorageSync(PARTNER_REFERRAL_TRACKED_KEY, true)
  uni.setStorageSync(PARTNER_REFERRAL_CODE_KEY, '')
  uni.removeStorageSync(LOGIN_INVITE_CODE_KEY)
}

export function savePartnerReferralInviteCode(inviteCode) {
  const normalized = String(inviteCode || '').trim().toUpperCase()
  uni.setStorageSync(PARTNER_REFERRAL_TRACKED_KEY, true)
  uni.setStorageSync(PARTNER_REFERRAL_CODE_KEY, normalized)
  if (normalized) {
    uni.setStorageSync(LOGIN_INVITE_CODE_KEY, normalized)
  } else {
    uni.removeStorageSync(LOGIN_INVITE_CODE_KEY)
  }
}

export function getPartnerReferralPurchaseCode() {
  if (!uni.getStorageSync(PARTNER_REFERRAL_TRACKED_KEY)) {
    return ''
  }
  return String(uni.getStorageSync(PARTNER_REFERRAL_CODE_KEY) || '').trim().toUpperCase()
}
