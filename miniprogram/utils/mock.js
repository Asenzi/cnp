/**
 * 本地兜底数据
 *
 * 目的：后端不可达时页面依然能完整走通流程，便于在开发者工具里验证
 * 交互与视觉，而不是对着白屏排查。真实联调时把 app.js 的
 * globalData.mockEnabled 置为 false 即可完全走真实接口。
 */

const NAMES = [
  '陈嘉铭', '林薇', '周子墨', '苏晴', '何一帆', '郑允', '吴桐', '黄宥辰',
  '李承泽', '徐若涵', '高维', '马晓东', '沈亦航', '罗曼', '谢予安', '曾书宁',
  '邓浩然', '唐悦', '曹铭轩', '许清和'
]

const INDUSTRIES = [
  '人工智能', '智能制造', '新能源汽车', '生物医药', '跨境电商', '企业服务',
  '文化传媒', '金融投资', '教育培训', '建筑设计', '医疗健康', '消费零售'
]

const CITIES = ['深圳', '广州', '上海', '北京', '杭州', '成都', '武汉', '南京', '苏州', '西安']

const INTROS = [
  '专注 AI 应用层落地，正在寻找供应链与渠道方向的合作伙伴',
  '十年制造业数字化转型经验，手里有多个智能工厂改造案例',
  '新能源三电系统出身，希望结识整车厂与 Tier1 的朋友',
  '生物医药 CMC 方向，乐意交流临床申报与产业化经验',
  '跨境电商独立站操盘，擅长流量投放与海外仓选址',
  '做企业服务 SaaS 第 6 年，正在搭建渠道代理体系',
  '内容 IP 孵化与短视频矩阵，寻找品牌方联合出品机会',
  '早年做 PE/VC，现在主要看硬科技早期项目',
  '职业教育赛道创业者，关注产教融合与实训基地',
  '建筑设计院出身，转型做城市更新与旧改运营'
]

const ROLES = [
  '创始人', '联合创始人', '合伙人', '技术负责人', '市场总监',
  '产品经理', '投资经理', '运营负责人', '供应链总监'
]

const pick = (list, index) => list[index % list.length]

/** 造一条稳定的假用户记录（同 index 永远返回同一条，便于反复比对视觉） */
function buildRawMember(index, cityName) {
  const seed = index + 1
  return {
    user_id: `mock_user_${seed}`,
    nickname: pick(NAMES, index),
    avatar_url: '',
    city_name: cityName || pick(CITIES, index),
    industry_label: pick(INDUSTRIES, index),
    intro: pick(INTROS, index),
    distance_text: seed <= 3 ? `${(seed * 1.7).toFixed(1)}km` : '',
    is_verified: seed % 3 !== 0,
    is_member: seed % 4 === 0,
    is_circle_owner: seed % 6 === 0,
    is_followed: seed % 5 === 0,
    post_count: (seed * 3) % 17,
    score: 90 - (seed % 20),
    active_text: seed % 2 === 0 ? '3 天内活跃' : '本周活跃',
    reason_tags: seed % 3 === 0 ? ['同行业', '同城'] : ['推荐'],
    reason_detail: {
      shared_circle_names: seed % 4 === 0 ? ['粤港澳创业者联盟'] : [],
      shared_connection_source: seed % 4 === 0 ? '二度人脉' : ''
    }
  }
}

export function mockRecommendations(params = {}) {
  const keyword = String(params.keyword || '').trim()
  const cityName = String(params.city_name || '').trim()
  const industryLabel = String(params.industry_label || '').trim()
  const limit = Number(params.limit || 20)
  const cursor = String(params.cursor || '')
  const offset = cursor ? Number(cursor) : 0

  let items = []
  for (let i = 0; i < limit; i += 1) {
    items.push(buildRawMember(offset + i, cityName))
  }

  if (keyword) {
    items = items.filter((item) => {
      return String(item.nickname).indexOf(keyword) >= 0
        || String(item.industry_label).indexOf(keyword) >= 0
        || String(item.intro).indexOf(keyword) >= 0
    })
  }

  if (industryLabel) {
    items = items.filter((item) => item.industry_label === industryLabel)
  }

  const nextOffset = offset + limit
  const hasMore = nextOffset < 60

  return {
    items,
    request_id: `mock_req_${Date.now()}`,
    next_cursor: hasMore ? String(nextOffset) : '',
    has_more: hasMore
  }
}

const RESOURCE_TITLES = [
  '寻找 SaaS 方向的天使轮投资方',
  '可提供跨境电商供应链资源',
  '诚邀制造业数字化转型合作',
  '出让闲置的线下活动场地资源',
  '招募短视频内容运营合伙人',
  '共享深圳南山办公工位 20 个',
  '寻求靠谱的代账与法务服务商',
  '提供企业级 AI 客服解决方案'
]

const RESOURCE_DESCRIPTIONS = [
  '团队来自头部出海公司，产品已跑通 PMF，月流水稳定增长，希望对接产业资源方。',
  '深耕行业多年，资源稳定可落地，欢迎有实际需求的伙伴详聊，支持长期合作。',
  '目前用户规模持续扩大，希望与渠道方、供应链方建立深度合作，互利共赢。'
]

const RESOURCE_INDUSTRIES = ['互联网 / AI', '市场 / 品牌 / 公关', '销售', '产品', '设计 / 传媒']

function buildRawResource(index) {
  const seed = Number(index || 0)
  const mode = seed % 3 === 0 ? 'resource' : 'cooperate'
  return {
    post_code: `mock_post_${seed + 1}`,
    mode,
    title: RESOURCE_TITLES[seed % RESOURCE_TITLES.length],
    description: RESOURCE_DESCRIPTIONS[seed % RESOURCE_DESCRIPTIONS.length],
    industry_label: RESOURCE_INDUSTRIES[seed % RESOURCE_INDUSTRIES.length],
    time_text: `${(seed % 24) + 1} 小时前`,
    view_count: 120 + seed * 17,
    collect_count: (seed % 9) + 1,
    comment_count: seed % 5,
    is_collected: seed % 4 === 0
  }
}

/** 资源 feed 兜底数据，形参与 getResourceFeed 一致 */
export function mockResourceFeed(params = {}) {
  const keyword = String(params.keyword || '').trim()
  const industryLabel = String(params.industry_label || '').trim()
  const limit = Number(params.limit || 20)
  const cursor = String(params.cursor || '')
  const offset = cursor ? Number(cursor) : 0

  let items = []
  for (let i = 0; i < limit; i += 1) {
    items.push(buildRawResource(offset + i))
  }

  if (keyword) {
    items = items.filter((item) => {
      return String(item.title).indexOf(keyword) >= 0
        || String(item.description).indexOf(keyword) >= 0
    })
  }

  if (industryLabel) {
    items = items.filter((item) => item.industry_label === industryLabel)
  }

  const nextOffset = offset + limit
  const hasMore = nextOffset < 60

  return {
    items,
    request_id: `mock_req_${Date.now()}`,
    next_cursor: hasMore ? String(nextOffset) : '',
    has_more: hasMore
  }
}

const CIRCLE_NAMES = [
  '粤港澳创业者联盟', '硬科技投资圈', '深圳产品经理圈子', '跨境电商增长营',
  '智能制造供应链圈', '新能源三电交流', '品牌出海实战派', '医疗健康产业圈',
  'AI 应用落地小组', '企业服务渠道联盟'
]

const CIRCLE_DESCRIPTIONS = [
  '每周一次线下闭门分享，聚焦早期项目的融资与商业化路径',
  '只聊硬科技：半导体、新材料、精密制造，拒绝空泛赛道讨论',
  '产品经理互助社区，简历互推、案例复盘、需求拆解都在这里',
  '独立站与平台卖家共建的选品、投放、海外仓资源共享圈',
  '工厂数字化改造的一线经验库，含供应商名录与踩坑清单'
]

/** 圈子发现流兜底数据，形参与 getDiscoverCircles 一致 */
export function mockDiscoverCircles(params = {}) {
  const keyword = String(params.keyword || '').trim()
  const industryLabel = String(params.industry_label || '').trim()
  const cityName = String(params.city_name || '').trim()
  const limit = Number(params.limit || 20)
  // 分页游标：真实接口用 offset，behavior 翻页时传 cursor，两者都支持
  const cursor = String(params.cursor || '')
  const offset = cursor ? Number(cursor) : Math.max(Number(params.offset || 0), 0)

  let items = []
  for (let i = 0; i < limit; i += 1) {
    const seed = offset + i
    items.push({
      circle_code: `mock_circle_${seed}`,
      name: pick(CIRCLE_NAMES, seed),
      description: pick(CIRCLE_DESCRIPTIONS, seed),
      industry_label: pick(INDUSTRIES, seed),
      owner_city_name: cityName || pick(CITIES, seed),
      owner_nickname: pick(NAMES, seed),
      owner_avatar_url: '',
      owner_is_verified: seed % 3 !== 0,
      member_count: 120 + seed * 37,
      post_count: 20 + seed * 9,
      collect_count: seed % 11,
      is_collected: seed % 4 === 0,
      avatar_url: ''
    })
  }

  if (keyword) {
    items = items.filter((item) => {
      return String(item.name).indexOf(keyword) >= 0
        || String(item.description).indexOf(keyword) >= 0
    })
  }

  if (industryLabel) {
    items = items.filter((item) => item.industry_label === industryLabel)
  }

  const nextOffset = offset + limit
  const hasMore = nextOffset < 60

  return {
    items,
    request_id: `mock_circle_${Date.now()}`,
    next_cursor: hasMore ? String(nextOffset) : '',
    has_more: hasMore
  }
}

/** 圈子详情兜底数据，字段形态与 getCircleDetail 返回一致 */
export function mockCircleDetail(circleCode) {
  const numeric = String(circleCode || '').replace(/\D/g, '')
  const seed = numeric ? Number(numeric) : 1
  const paid = seed % 3 === 0

  return {
    circle_code: circleCode,
    name: pick(CIRCLE_NAMES, seed),
    description: pick(CIRCLE_DESCRIPTIONS, seed),
    industry_label: pick(INDUSTRIES, seed),
    owner_city_name: pick(CITIES, seed),
    cover_url: '',
    avatar_url: '',
    member_count: 120 + seed * 37,
    post_count: 20 + seed * 9,
    join_type: paid ? 'paid' : (seed % 2 === 0 ? 'review' : 'free'),
    join_price: paid ? 99 : 0,
    collect_count: seed % 11,
    is_collected: seed % 4 === 0,
    is_joined: false,
    join_request_status: '',
    join_payment_status: '',
    notice: '欢迎加入本圈子！本周五将举办线下对接会，名额有限，请关注活动板块报名。',
    owner: {
      user_id: `mock_user_${(seed % 20) + 1}`,
      nickname: pick(NAMES, seed),
      avatar_url: '',
      intro: '十年行业经验，正在搭建资源共享网络'
    }
  }
}

/** 圈子成员兜底数据 */
export function mockCircleMembers(params = {}) {
  const limit = Number(params.limit || 20)
  const items = []
  for (let i = 0; i < limit; i += 1) {
    const raw = buildRawMember(i)
    raw.is_owner = i === 0
    items.push(raw)
  }
  return { items }
}

/** 圈子动态兜底数据，字段形态与 getCirclePosts 返回一致 */
export function mockCirclePosts(params = {}) {
  const limit = Number(params.limit || 20)
  const items = []
  for (let i = 0; i < limit; i += 1) {
    items.push(buildRawResource(i))
  }
  return { items }
}

export function mockFilterOptions() {

  return {
    cities: CITIES,
    industries: INDUSTRIES
  }
}

export function mockLoginResult(payload = {}) {
  return {
    access_token: 'mock_token_' + Date.now(),
    refresh_token: 'mock_refresh_' + Date.now(),
    is_new_user: false,
    expires_in: 7200,
    user_info: {
      user_id: 'mock_user_self',
      nickname: '我',
      avatar_url: '',
      city_name: String(payload.city_name || '深圳'),
      industry_label: '企业服务',
      intro: '这是本地兜底数据生成的个人档案',
      is_verified: true,
      is_member: false,
      is_circle_owner: false,
      post_count: 6,
      follower_count: 128,
      following_count: 42
    }
  }
}

export function mockProfile(userId) {
  const numericId = String(userId || '').replace(/\D/g, '')
  const index = numericId ? Number(numericId) - 1 : 0
  const raw = buildRawMember(index < 0 ? 0 : index)

  return {
    user_id: raw.user_id,
    nickname: raw.nickname,
    avatar_url: raw.avatar_url,
    city_name: raw.city_name,
    industry_label: raw.industry_label,
    role: pick(ROLES, index),
    intro: raw.intro,
    is_verified: raw.is_verified,
    is_member: raw.is_member,
    is_circle_owner: raw.is_circle_owner,
    is_followed: raw.is_followed,
    post_count: raw.post_count,
    follower_count: 130 + index * 7,
    following_count: 40 + index * 3,
    circle_names: index % 2 === 0 ? ['粤港澳创业者联盟', '硬科技投资圈'] : ['深圳产品经理圈子'],
    contact: {
      phone: '',
      wechat: '',
      locked: true
    },
    active_text: raw.active_text
  }
}

export function mockFollowResult(desiredFollow) {
  return {
    is_followed: Boolean(desiredFollow)
  }
}
