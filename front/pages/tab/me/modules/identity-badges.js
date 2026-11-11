// Identity fields come from the current-user profile API.
export function buildIdentityBadges(user, verified, circleOwner) {
  const badges = []
  if (verified) badges.push({ key: 'verified', label: '已认证', icon: '/static/me-reference/verified.png' })
  if (circleOwner) badges.push({ key: 'circle-owner', label: '圈主', icon: '/static/icon/leader.png' })
  if (user.partner_type === 'salon_owner') badges.push({ key: 'salon-owner', label: '沙龙主理人', icon: '/static/icon/salon-owner.svg' })
  if (user.partner_type === 'city_partner') badges.push({ key: 'city-partner', label: '城市合伙人', icon: '/static/icon/city-partner.svg' })
  return badges
}
