const enabled = value => [true, 1, '1', 'true', 'active'].includes(value)

export function mapCollectedContact(item = {}) {
  const id = String(item.user_id || item.userId || '').trim()
  const name = String(item.nickname || '').trim() || '未命名用户'
  const bio = String(item.intro || '').trim()
  const company = String(item.company_name || item.company || '').trim()
  const job = String(item.job_title || '').trim()
  const city = String(item.city_name || '').trim()
  return {
    id, userId: id, businessUserId: id, name,
    avatar: item.avatar_url || 'https://cos.cnptec.site/static/logo.png',
    detail: [job, company].filter(Boolean).join(' · '), bio,
    detailLine: company || '暂未填写行业',
    metaLine: [job, city].filter(Boolean).join(' | '),
    verifyType: enabled(item.is_verified) || enabled(item.real_name_verified) ? 'lv1' : '',
    memberEnabled: enabled(item.is_member) || enabled(item.member_opened),
    circleOwner: enabled(item.is_circle_owner),
    circleTags: bio ? [bio] : [],
    distanceText: item.distance_text || '',
    activeText: item.active_text || '最近活跃'
  }
}

export function mapCollectedCircle(item = {}) {
  const code = String(item.circleCode || item.circle_code || item.id || '').trim()
  return {
    ...item,
    id: code, circleCode: code,
    title: item.title || item.name || '',
    coverImage: item.coverImage || item.avatar_url || item.cover_url || '',
    industryLabel: item.industryLabel || item.industry_label || '',
    members: Number(item.members ?? item.member_count ?? 0),
    posts: Number(item.posts ?? item.post_count ?? 0),
    views: Number(item.view_count ?? item.visit_count ?? 0),
    collected: true
  }
}
